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

from formencode import Schema, validators, api, foreach
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet)
from pyquest.renderer import render
from pyquest.validation import (PageSchema, qsheet_to_schema, flatten_invalid,
                                ValidationState, XmlValidator)

class QSheetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    content = XmlValidator('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>')
    schema = XmlValidator('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>', strip_wrapper=False)

class QSheetOrderSchema(Schema):
    qsid = foreach.ForEach(validators.Int())

@view_config(route_name='survey.qsheet')
@render({'text/html': 'backend/qsheet/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
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
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                validator = QSheetSchema()
                try:
                    if 'content' in request.POST:
                        request.POST['schema'] = request.POST['content']
                    params = validator.to_python(request.POST)
                    if params['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        qsheet = QSheet(survey_id=request.matchdict['sid'],
                                        title=params['title'],
                                        content=params['content'],
                                        schema = pickle.dumps(qsheet_to_schema(params['schema'])))
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
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            example = {'did': 0}
            if survey.all_items:
                example['did'] = survey.all_items[0].id
                for attr in survey.all_items[0].attributes:
                    example[attr.key] = attr.value
            if request.method == 'POST':
                schema = pickle.loads(str(qsheet.schema))
                validator = PageSchema(schema, [example])
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
def edit_qsheet(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                validator = QSheetSchema()
                try:
                    if 'content' in request.POST:
                        request.POST['schema'] = request.POST['content']
                    params = validator.to_python(request.POST)
                    if params['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                    with transaction.manager:
                        qsheet.title = params['title']
                        qsheet.content = params['content']
                        qsheet.schema = pickle.dumps(qsheet_to_schema(params['schema']))
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
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                if 'csrf_token' not in request.POST or request.POST['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                with transaction.manager:
                    dbsession.delete(qsheet)
                request.session.flash('Survey page deleted', 'info')
                raise HTTPFound(request.route_url('survey.edit',
                                                  sid=request.matchdict['sid']))
            else:
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
