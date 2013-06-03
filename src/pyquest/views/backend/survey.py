# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
import transaction

from formencode import Schema, validators, api, variabledecode
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pywebtools.auth import is_authorised
from pywebtools.renderer import render

from pyquest import helpers
from pyquest.views.backend.qsheet import load_qsheet_from_xml, load_transition_from_xml
from pyquest.helpers.data import create_data_item_sets
from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheetTransition, QSheet,
                            Participant, QSheetAttribute, Question,
    QuestionAttributeGroup, QuestionAttribute, DataItem, DataItemAttribute,
    DataItemControlAnswer)
from pyquest.validation import XmlValidator

class NewSurveySchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    summary = validators.UnicodeString()
    language = validators.OneOf(['en', 'de'])

class SurveySchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    start = validators.Int(if_missing=None, if_empty=None)
    summary = validators.UnicodeString()
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()
    language = validators.OneOf(['en', 'de'])
    
    pre_validators = [variabledecode.NestedVariables()]

class SurveyStatusSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    status = validators.OneOf(['develop', 'testing', 'running', 'paused', 'finished'])

class SurveyDuplicateSchema(Schema):
    csrf_token = validators.UnicodeString(note_empty=True)
    title = validators.UnicodeString(not_empty=True)
    
@view_config(route_name='survey')
@render({'text/html': 'backend/survey/index.html'})
def index(request):
    user = current_user(request)
    if is_authorised(':user.logged-in', {'user': user}):
        return {'surveys': user.surveys}
    else:
        redirect_to_login(request)

@view_config(route_name='survey.view')
@render({'text/html': 'backend/survey/view.html'})
def view(request):
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

@view_config(route_name='survey.new')
@render({'text/html': 'backend/survey/new.html'})
def new(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = Survey()
    if is_authorised(':user.has_permission("survey.new")', {'user': user}):
        if request.method == 'POST':
            try:
                params = NewSurveySchema().to_python(request.POST)
                check_csrf_token(request, params)
                with transaction.manager:
                    survey.title = params['title']
                    survey.summary = params['summary']
                    survey.styles = ''
                    survey.scripts = ''
                    survey.status = 'develop'
                    survey.owned_by = user.id
                    survey.language = params['language']
                    dbsession.add(survey)
                    dbsession.flush()
                    sid = survey.id
                request.session.flash('Survey created', 'info')
                raise HTTPFound(request.route_url('survey.view', sid=sid))
            except api.Invalid as e:
                e.params = request.POST
                return {'survey': survey,
                        'e': e}
        else:
            return {'survey': survey}
    else:
        redirect_to_login(request)

def load_survey_from_xml(owner, dbsession, doc):
    survey = Survey(title=doc.attrib['title'], status='develop')
    survey.owner = owner
    qsheets = {}
    for item in doc:
        if item.tag == '{http://paths.sheffield.ac.uk/pyquest}summary':
            survey.summary = item.text
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}language':
            survey.language = item.text
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}styles':
            survey.styles = item.text
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}scripts':
            survey.scripts = item.text
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}qsheet':
            qsheet = load_qsheet_from_xml(survey, item, dbsession)
            qsheets[qsheet.name] = qsheet
    for item in doc:
        if item.tag == '{http://paths.sheffield.ac.uk/pyquest}first_page':
            if item.text in qsheets:
                survey.start = qsheets[item.text]
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}transition':
            load_transition_from_xml(qsheets, item, dbsession)
    create_data_item_sets(dbsession, owner)
    return survey

@view_config(route_name='survey.import')
@render({'text/html': 'backend/survey/import.html'})
def import_survey(request):
    user = current_user(request)
    if is_authorised(':user.has_permission("survey.new")', {'user': user}):
        if request.method == 'POST':
            try:
                if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                    raise api.Invalid('Invalid XML file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
                doc = XmlValidator('%s').to_python(''.join(request.POST['source_file'].file))
                if doc.tag != '{http://paths.sheffield.ac.uk/pyquest}survey':
                    raise api.Invalid('Not a survey file', {}, None, error_dict={'source_file': 'Only complete surveys can be imported here.'})
                dbsession = DBSession()
                with transaction.manager:
                    survey = load_survey_from_xml(user, dbsession, doc)
                    dbsession.add(survey)
                    dbsession.flush()
                    survey_id = survey.id
                request.session.flash('Survey imported', 'info')
                raise HTTPFound(request.route_url('survey.view', sid=survey_id))
            except api.Invalid as e:
                e.params = request.POST
                return {'e': e}
        else:
            return {}
    else:
        redirect_to_login(request)

@view_config(route_name='survey.edit')
@render({'text/html': 'backend/survey/edit.html'})
def edit(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    schema = SurveySchema()
                    params = schema.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        survey.title = params['title']
                        survey.summary = params['summary']
                        survey.styles = params['styles']
                        survey.scripts = params['scripts']
                        survey.start_id = params['start']
                        survey.language = params['language']
                        dbsession.add(survey)
                    request.session.flash('Survey updated', 'info')
                    raise HTTPFound(request.route_url('survey.view',
                                                      sid=request.matchdict['sid']))
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

@view_config(route_name='survey.duplicate')
@render({'text/html': 'backend/survey/duplicate.html'})
def duplicate(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    check_csrf_token(request, request.POST)
                    params = SurveyDuplicateSchema().to_python(request.POST)
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        dupl_survey = Survey(title=params['title'],
                                             status='develop',
                                             owner=user,
                                             summary=survey.summary,
                                             styles=survey.styles,
                                             scripts=survey.scripts)
                        dbsession.add(dupl_survey)
                        qsheets = {}
                        for qsheet in survey.qsheets:
                            dupl_qsheet = QSheet(name=qsheet.name,
                                                 title=qsheet.title,
                                                 styles=qsheet.styles,
                                                 scripts=qsheet.scripts)
                            for attr in qsheet.attributes:
                                dupl_qsheet.attributes.append(QSheetAttribute(key=attr.key, value=attr.value))
                            questions = {}
                            for question in qsheet.questions:
                                dupl_question = Question(q_type=question.q_type,
                                                         name=question.name,
                                                         title=question.title,
                                                         required=question.required,
                                                         help=question.help,
                                                         order=question.order)
                                questions[dupl_question.name] = dupl_question
                                dupl_qsheet.questions.append(dupl_question)
                                for attr_group in question.attributes:
                                    dupl_attr_group = QuestionAttributeGroup(question=dupl_question,
                                                                             key=attr_group.key,
                                                                             label=attr_group.label,
                                                                             order=attr_group.order)
                                    for attr in attr_group.attributes:
                                        QuestionAttribute(attribute_group=dupl_attr_group,
                                                          key=attr.key,
                                                          label=attr.label,
                                                          value=attr.value,
                                                          order=attr.order)
                            for data_item in qsheet.data_items:
                                dupl_data_item = DataItem(qsheet=dupl_qsheet,
                                                          order=data_item.order,
                                                          control=data_item.control)
                                for attr in data_item.attributes:
                                    DataItemAttribute(data_item=dupl_data_item,
                                                      order=attr.order,
                                                      key=attr.key,
                                                      value=attr.value)
                                for control_answer in data_item.control_answers:
                                    if control_answer.question and control_answer.question.name in questions:
                                        DataItemControlAnswer(data_item=dupl_data_item,
                                                              question=questions[control_answer.question.name],
                                                              answer=control_answer.answer)
                            qsheets[dupl_qsheet.name] = dupl_qsheet
                            dupl_survey.qsheets.append(dupl_qsheet)
                        for qsheet in survey.qsheets:
                            if qsheet.next and qsheet.next[0] and qsheet.next[0].target:
                                if qsheet.name in qsheets and qsheet.next[0].target.name in qsheets:
                                    dbsession.add(QSheetTransition(source=qsheets[qsheet.name],
                                                                   target=qsheets[qsheet.next[0].target.name]))
                        if survey.start and survey.start.name in qsheets:
                            dupl_survey.start = qsheets[survey.start.name]
                        dbsession.flush()
                        survey_id = dupl_survey.id
                    request.session.flash('Survey duplicated', 'info')
                    raise HTTPFound(request.route_url('survey.view', sid=survey_id))
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

@view_config(route_name='survey.delete')
@render({'text/html': 'backend/survey/delete.html'})
def delete(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    check_csrf_token(request, request.POST)
                    with transaction.manager:
                        dbsession.delete(survey)
                    request.session.flash('Survey deleted', 'info')
                    raise HTTPFound(request.route_url('survey'))
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

@view_config(route_name='survey.preview')
@render({'text/html': 'backend/survey/preview.html'})
def preview(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            qsheets = [dbsession.query(QSheet).filter(QSheet.id==survey.start_id).first()]
            qids = [qsheets[0].id]
            while qsheets[-1]:
                if qsheets[-1].next and qsheets[-1].next[0].target and qsheets[-1].next[0].target.id not in qids:
                    qids.append(qsheets[-1].next[0].target.id)
                    qsheets.append(qsheets[-1].next[0].target)
                else:
                    qsheets.append(None)
            return {'survey': survey,
                    'qsheets': qsheets[:-1],
                    'participant': Participant(id=-1)}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.status')
@render({'text/html': 'backend/survey/status.html'})
def status(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    params = SurveyStatusSchema().to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        if survey.status == 'testing' and params['status'] == 'develop':
                            survey.participants = []
                            for qsheet in survey.qsheets:
                                for data_item in qsheet.data_items:
                                    data_item.counts = []
                                    dbsession.add(data_item)
                        survey.status = params['status']
                        dbsession.add(survey)
                    request.session.flash('Survey now %s' % helpers.survey.status(params['status'], True), 'info')
                    if params['status'] == 'testing':
                        raise HTTPFound(request.route_url('survey.run',
                                                          sid=request.matchdict['sid']))
                    elif params['status'] == 'finished':
                        raise HTTPFound(request.route_url('survey.results',
                                                          sid=request.matchdict['sid']))
                    else:
                        raise HTTPFound(request.route_url('survey.view',
                                                          sid=request.matchdict['sid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'status': request.params['status'],
                            'e': e}
            else:
                if 'status' not in request.params:
                    raise HTTPFound(request.route_url('survey.view', sid=request.matchdict['sid']))
                return {'survey': survey,
                        'status': request.params['status']}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()


@view_config(route_name='survey.export')
@view_config(route_name='survey.export.ext')
@render({'text/html': 'backend/survey/export.html',
         'application/xml': 'backend/survey/export.xml'})
def export(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
