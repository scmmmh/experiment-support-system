# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2012

@author: mhall
'''
try:
    import cPickle as pickle
except:
    import pickle
import transaction

from formencode import Schema, validators, api, foreach, variabledecode, compound
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_
from pywebtools.auth import is_authorised

from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet)
from pyquest.renderer import render
from pyquest.validation import (PageSchema, flatten_invalid,
                                ValidationState, XmlValidator)

class QSheetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    content = XmlValidator('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>')
    schema = XmlValidator('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>', strip_wrapper=False)
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()

class QSheetVisualTextSchema(Schema):
    text = validators.UnicodeString()
    order = validators.Int()
    
class QSheetVisualQuestionSchema(Schema):
    type = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString()
    help = validators.UnicodeString()
    order = validators.Int()
    required = validators.StringBool(if_missing=False)
    
    allow_extra_fields=True
    
class QSheetVisualSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    item = foreach.ForEach(compound.Any(QSheetVisualQuestionSchema(), QSheetVisualTextSchema()))
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()
    
    pre_validators = [variabledecode.NestedVariables()]
    
class QSheetOrderSchema(Schema):
    qsid = foreach.ForEach(validators.Int())

@view_config(route_name='survey.qsheet')
@render({'text/html': 'backend/qsheet/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.new')
@render({'text/html': 'backend/qsheet/new.html'})
def new_qsheet(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                validator = QSheetSchema()
                try:
                    if 'content' in request.POST:
                        request.POST['schema'] = request.POST['content']
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        qsheet = QSheet(survey_id=request.matchdict['sid'],
                                        name=params['name'],
                                        title=params['title'],
                                        content=params['content'],
                                        schema = pickle.dumps(qsheet_to_schema(params['schema'])),
                                        styles=params['styles'],
                                        scripts=params['scripts'])
                        dbsession.add(qsheet)
                        dbsession.flush()
                        qsid = qsheet.id
                    request.session.flash('Survey page added', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.view',
                                                      sid=request.matchdict['sid'],
                                                      qsid=qsid))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'e': e}
            else:
                return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()


@view_config(route_name='survey.qsheet.view')
@render({'text/html': 'backend/qsheet/view.html'})
def view(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            example = {'did': 0}
            if survey.data_items:
                example['did'] = survey.data_items[0].id
                for attr in survey.data_items[0].attributes:
                    example[attr.key] = attr.value
            if request.method == 'POST':
                validator = PageSchema(qsheet, [example])
                try:
                    validator.to_python(request.POST, ValidationState(request=request))
                except api.Invalid as ie:
                    ie = flatten_invalid(ie)
                    ie.params = request.POST
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'example': example,
                            'e': ie}
            return {'survey': survey,
                    'qsheet': qsheet,
                    'example': example}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.edit')
@render({'text/html': 'backend/qsheet/edit.html'})
def edit(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    params = QSheetVisualSchema().to_python(request.POST)
                    items = params['item']
                    items.sort(key=lambda i: i['order'])
                    schema = []
                    for item in items:
                        if 'type' in item:
                            # Need to correctly set the "required" field.
                            # Numbers have more attributes. Need to be factored out
                            # Add all the other types
                            if item['type'] == 'short_text':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                            elif item['type'] == 'number':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                            elif item['type'] == 'email':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                            elif item['type'] == 'url':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                            elif item['type'] == 'date':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                            elif item['type'] == 'time':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                            elif item['type'] == 'datetime':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                            elif item['type'] == 'month':
                                schema.append('<pq:short_text name="%s" title="%s" help="%s"/>' % (item['name'], item['title'], item['help']))
                        elif 'text' in item:
                            schema.append(item['text'])
                    with transaction.manager:
                        qsheet.name = params['name']
                        qsheet.title = params['title']
                        qsheet.content = '\n'.join(schema)
                        qsheet.schema = pickle.dumps(qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % ('\n'.join(schema))))
                        qsheet.styles = params['styles']
                        qsheet.scripts = params['scripts']
                        dbsession.add(qsheet)
                    request.session.flash('Survey page updated', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                      sid=request.matchdict['sid'],
                                                      qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'e': e}
            else:
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.edit.fragment')
@render({'text/html': 'backend/qsheet/edit_fragment.html'})
def qsheet_fragment(request):
    return {'item': 'Test'}

@view_config(route_name='survey.qsheet.edit.source')
@render({'text/html': 'backend/qsheet/edit_source.html'})
def edit_source(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                validator = QSheetSchema()
                try:
                    if 'content' in request.POST:
                        request.POST['schema'] = request.POST['content']
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        qsheet.name = params['name']
                        qsheet.title = params['title']
                        qsheet.content = params['content']
                        qsheet.schema = pickle.dumps(qsheet_to_schema(params['schema']))
                        qsheet.styles = params['styles']
                        qsheet.scripts = params['scripts']
                        dbsession.add(qsheet)
                    request.session.flash('Survey page updated', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                      sid=request.matchdict['sid'],
                                                      qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'e': e}
            else:
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.delete')
@render({'text/html': 'backend/qsheet/delete.html'})
def delete_qsheet(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                with transaction.manager:
                    dbsession.delete(qsheet)
                request.session.flash('Survey page deleted', 'info')
                raise HTTPFound(request.route_url('survey.pages',
                                                  sid=request.matchdict['sid']))
            else:
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
