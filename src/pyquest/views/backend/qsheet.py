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
from pyquest.helpers.qsheet import get_q_attr, get_attr_groups, get_qg_attr
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

class QSheetTextSchema(Schema):
    id = validators.Int()
    text = validators.UnicodeString()
    order = validators.Int()
    
class QSheetBasicQuestionSchema(Schema):
    id = validators.Int(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    help = validators.UnicodeString()
    required = validators.StringBool(if_missing=False)
    order = validators.Int(not_empty=True)

class QSheetNumberQuestionSchema(QSheetBasicQuestionSchema):
    min = validators.Int()
    max = validators.Int()

class QSheetAnswerSchema(Schema):
    id = validators.Int(not_empty=True)
    value = validators.UnicodeString(not_empty=True)
    label = validators.UnicodeString()
    order = validators.Int(not_empty=True)

class QSheetSubQuestionSchema(Schema):
    id = validators.Int(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    label = validators.UnicodeString()
    order = validators.Int(not_empty=True)
    
class QSheetDynamicSchema(Schema):
    pass

class QSheetConfirmQuestionSchema(QSheetBasicQuestionSchema):
    value = validators.UnicodeString(not_empty=True)
    label = validators.UnicodeString()

class QSheetVisualSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
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
                    schema = QSheetVisualSchema()
                    for question in qsheet.questions:
                        if question.type == 'text':
                            schema.add_field(unicode(question.id), QSheetTextSchema())
                        elif question.type == 'number':
                            schema.add_field(unicode(question.id), QSheetNumberQuestionSchema())
                        elif question.type == 'confirm':
                            schema.add_field(unicode(question.id), QSheetConfirmQuestionSchema())
                        else:
                            sub_schema = QSheetBasicQuestionSchema()
                            if question.type in ['rating', 'rating_group', 'single_list', 'single_select', 'multichoice', 'multichoice_group', 'ranking']:
                                answer_schema = QSheetDynamicSchema()
                                for attr_group in get_attr_groups(question, 'answer'):
                                    answer_schema.add_field(unicode(attr_group.id), QSheetAnswerSchema())
                                sub_schema.add_field('answer', answer_schema)
                            if question.type in ['rating_group', 'multichoice_group']:
                                sub_quest_schema = QSheetDynamicSchema()
                                for attr_group in get_attr_groups(question, 'subquestion'):
                                    sub_quest_schema.add_field(unicode(attr_group.id), QSheetSubQuestionSchema())
                                sub_schema.add_field('sub_quest', sub_quest_schema)
                            schema.add_field(unicode(question.id), sub_schema)
                    params = schema.to_python(request.POST)
                    with transaction.manager:
                        qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                     QSheet.survey_id==request.matchdict['sid'])).first()
                        qsheet.name = params['name']
                        qsheet.title = params['title']
                        qsheet.styles = params['styles']
                        qsheet.scripts = params['scripts']
                        for question in qsheet.questions:
                            q_params = params[unicode(question.id)]
                            if question.type == 'text':
                                get_q_attr(question, 'text.text').value = q_params['text']
                            else:
                                question.name = q_params['name']
                                question.title = q_params['title']
                                question.help = q_params['help']
                                question.required = q_params['required']
                                question.order = q_params['order']
                                if question.type == 'number':
                                    get_q_attr(question, 'further.min').value = q_params['min']
                                    get_q_attr(question, 'further.max').value = q_params['max']
                                elif question.type == 'confirm':
                                    get_q_attr(question, 'further.value').value = q_params['value']
                                    get_q_attr(question, 'further.label').value = q_params['label']
                                else:
                                    if question.type in ['rating', 'rating_group', 'single_list', 'single_select', 'multichoice', 'multichoice_group', 'ranking']:
                                        for attr_group in get_attr_groups(question, 'answer'):
                                            get_qg_attr(attr_group, 'value').value = q_params['answer'][unicode(attr_group.id)]['value']
                                            get_qg_attr(attr_group, 'label').value = q_params['answer'][unicode(attr_group.id)]['label'] 
                                            attr_group.order = q_params['answer'][unicode(attr_group.id)]['order']
                                    if question.type in ['rating_group', 'multichoice_group']:
                                        for attr_group in get_attr_groups(question, 'subquestion'):
                                            get_qg_attr(attr_group, 'name').value = q_params['sub_quest'][unicode(attr_group.id)]['name']
                                            get_qg_attr(attr_group, 'label').value = q_params['sub_quest'][unicode(attr_group.id)]['label'] 
                                            attr_group.order = q_params['sub_quest'][unicode(attr_group.id)]['order']
                        dbsession.add(qsheet)
                    request.session.flash('Survey page updated', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                      sid=request.matchdict['sid'],
                                                      qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e = flatten_invalid(e)
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
