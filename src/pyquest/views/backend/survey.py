# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
import transaction

from formencode import Schema, validators, api, variabledecode, foreach
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from pywebtools.auth import is_authorised
from pywebtools.renderer import render
from sqlalchemy import desc, and_
from StringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED

from pyquest import helpers
from pyquest.views.backend.data import load_csv_file
from pyquest.views.backend.qsheet import (load_qsheet_from_xml,
                                          load_transition_from_xml)
from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, Participant,
                            Notification, DataSetRelation)
from pyquest.validation import XmlValidator

class NewSurveySchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    summary = validators.UnicodeString()
    language = validators.OneOf(['en', 'de'])
    public = validators.Bool()

class NotificationSchema(Schema):
    id = validators.Int(if_missing=0)
    ntype = validators.UnicodeString()
    value = validators.Int(if_missing=0)
    recipient = validators.UnicodeString()

class SurveySchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    start = validators.Int(if_missing=None, if_empty=None)
    summary = validators.UnicodeString()
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()
    language = validators.OneOf(['en', 'de'])
    public = validators.Bool()
    notifications = foreach.ForEach(NotificationSchema())

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
            stats = {'completed': dbsession.query(Participant).filter(and_(Participant.survey_id==survey.id,
                                                                           Participant.completed==True)).count()}
            return {'survey': survey,
                    'stats': stats}
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
                    survey.public = params['public']
                    dbsession.add(survey)
                    dbsession.flush()
                    sid = survey.id
                request.session.flash('Experiment created', 'info')
                raise HTTPFound(request.route_url('survey.view', sid=sid))
            except api.Invalid as e:
                e.params = request.POST
                return {'survey': survey,
                        'e': e}
        else:
            return {'survey': survey}
    else:
        redirect_to_login(request)

def load_survey_from_xml(owner, dbsession, doc, zip_file):
    survey = Survey(title=doc.attrib['title'], status='develop')
    survey.owner = owner
    qsheets = {}
    for item in doc:
        if item.tag == '{%s}summary' % (XmlValidator.namespace):
            survey.summary = item.text
        elif item.tag == '{%s}language' % (XmlValidator.namespace):
            survey.language = item.text
        elif item.tag == '{%s}styles' % (XmlValidator.namespace):
            survey.styles = item.text
        elif item.tag == '{%s}scripts' % (XmlValidator.namespace):
            survey.scripts = item.text
        elif item.tag == '{%s}pages' % (XmlValidator.namespace):
            for page in item:
                qsheet = load_qsheet_from_xml(survey, page, dbsession)
                qsheets[qsheet.name] = qsheet
        elif item.tag == '{%s}data' % (XmlValidator.namespace):
            data_sets = {}
            for data in item:
                if data.tag == '{%s}data_set' % (XmlValidator.namespace):
                    data_set = load_csv_file(StringIO(zip_file.read('%s.csv' % (data.attrib['name']))), data.attrib['name'], survey, dbsession)
                    data_sets[data_set.name] = data_set
                    for attach in data:
                        if attach.tag == '{%s}attached_to' % (XmlValidator.namespace):
                            if attach.text in qsheets:
                                qsheets[attach.text].data_set = data_set
            for data in item:
                if data.tag == '{%s}permutation_set' % (XmlValidator.namespace):
                    relations = 0
                    for relation in data:
                        if relation.tag == '{%s}relation' % (XmlValidator.namespace):
                            if relation.attrib['object'] in data_sets:
                                relations = relations + 1
                    if relations == 2:
                        data_set = load_csv_file(StringIO(zip_file.read('%s.csv' % (data.attrib['name']))), data.attrib['name'], survey, dbsession)
                        data_set.type = 'permutationset'
                        for child in data:
                            if child.tag == '{%s}attached_to' % (XmlValidator.namespace):
                                if child.text in qsheets:
                                    qsheets[child.text].data_set = data_set
                            elif child.tag == '{%s}relation' % (XmlValidator.namespace):
                                dbsession.add(DataSetRelation(subject=data_set,
                                                              rel=child.attrib['rel'],
                                                              object=data_sets[child.attrib['object']],
                                                              _data=child.text.strip()))
                    else:
                        raise Exception('Permutation set must have exactly two relations')
    for item in doc:
        if item.tag == '{%s}first_page' % (XmlValidator.namespace):
            if item.text in qsheets:
                survey.start = qsheets[item.text]
        elif item.tag == '{%s}transitions' % (XmlValidator.namespace):
            for transition in item:
                load_transition_from_xml(qsheets, transition, dbsession)
    return survey

def load_survey_from_stream(stream, owner, dbsession):
    zip_file = ZipFile(stream)
    try:
        doc = XmlValidator('%s').to_python(zip_file.read('experiment.xml'))
        if doc.tag != '{%s}experiment' % (XmlValidator.namespace):
            raise api.Invalid('Not an experiment file', {}, None, error_dict={'source_file': 'Only complete experiments can be imported here.'})
        survey = load_survey_from_xml(owner, dbsession, doc, zip_file)
        dbsession.add(survey)
        return survey
    except Exception as e:
        raise api.Invalid(str(e), {}, None, error_dict={'source_file': str(e)})

@view_config(route_name='survey.import')
@render({'text/html': 'backend/survey/import.html'})
def import_survey(request):
    user = current_user(request)
    if is_authorised(':user.has_permission("survey.new")', {'user': user}):
        if request.method == 'POST':
            try:
                if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                    raise api.Invalid('Invalid experiment file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
                dbsession = DBSession()
                with transaction.manager:
                    survey = load_survey_from_stream(request.POST['source_file'].file, user, dbsession)
                dbsession.add(survey)
                request.session.flash('Experiment imported', 'info')
                raise HTTPFound(request.route_url('survey.view', sid=survey.id))
                return {}
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
                        survey.public = params['public']

                        for notification in survey.notifications:
                            n_param = next(n_param for n_param in params['notifications'] if n_param['id'] == notification.id)
                            notification.ntype = n_param['ntype']
                            notification.value = n_param['value']
                            notification.recipient = n_param['recipient']

                        dbsession.add(survey)
                    request.session.flash('Experiment updated', 'info')
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

@view_config(route_name='survey.edit.delete_notification')
@render({'text/html': 'backend/survey/notifications.html'})
def edit_delete_notification(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    to_delete = dbsession.query(Notification).filter(Notification.survey_id==survey.id).order_by(desc(Notification.id)).first()
    if to_delete:
        survey.notifications.remove(to_delete)

    return {'survey': survey}

@view_config(route_name='survey.edit.add_notification')
@render({'text/html': 'backend/survey/notifications.html'})
def edit_add_notification(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    new_notification = Notification(survey_id = survey.id, ntype='interval', value=60, recipient=survey.owner.email)
    survey.notifications.append(new_notification)
    dbsession.add(new_notification)
    dbsession.flush()

    return {'survey':survey}

@view_config(route_name='survey.duplicate')
@render({'text/html': 'backend/survey/duplicate.html'})
def duplicate(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    check_csrf_token(request, request.POST)
                    params = SurveyDuplicateSchema().to_python(request.POST)
                    exported_survey = export_experiment(request, survey)
                    with transaction.manager:
                        dupl_survey = load_survey_from_stream(exported_survey, user, dbsession)
                        dupl_survey.title = params['title']
                        dupl_survey.status = 'develop'
                    dbsession.add(dupl_survey)
                    request.session.flash('Experiment duplicated', 'info')
                    raise HTTPFound(request.route_url('survey.view', sid=dupl_survey.id))
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
                    request.session.flash('Experiment deleted', 'info')
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
                        dbsession.add(survey)
                        if survey.status == 'testing' and params['status'] == 'develop':
                            survey.participants = []
                            for qsheet in survey.qsheets:
                                if qsheet.data_set:
                                    for data_item in qsheet.data_set.items:
                                        data_item.counts = []
                                        dbsession.add(data_item)
                        if params['status'] == 'running':
                            for notification in survey.notifications:
                                dbsession.add(notification)
                                notification.timestamp = 0
                        survey.status = params['status']
                    request.session.flash('Experiment now %s' % helpers.survey.status(params['status'], True), 'info')
                    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                                  
                    if params['status'] == 'testing':
                        raise HTTPFound(request.route_url('survey.run',
                                                          seid=survey.external_id))
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

def export_experiment(request, survey):
    @render({'application/xml': 'backend/survey/export.xml'})
    def experiment_xml_file(request, survey):
        return {'survey': survey}
    @render({'text/csv': True})
    def data_set_file(request, data_set):
        columns = []
        rows = []
        if len(data_set.items) > 0:
            columns = ['id_', 'control_'] + [a.key.key.encode('utf-8') for a in data_set.items[0].attributes]
            for item in data_set.items:
                row = dict([(a.key.key.encode('utf-8'), a.value.encode('utf-8')) for a in item.attributes])
                row.update(dict([('control_', item.control), ('id_', item.id)]))
                rows.append(row)
        return {'columns': columns,
                'rows': rows}

    experiment = StringIO()
    zip_file = ZipFile(experiment, mode='w')
    zip_file.writestr('experiment.xml', experiment_xml_file(request, survey).body, compress_type=ZIP_DEFLATED)
    for data_set in survey.data_sets:
        zip_file.writestr('%s.csv' % (data_set.name), data_set_file(request, data_set).body, compress_type=ZIP_DEFLATED)
    for data_set in survey.permutation_sets:
        zip_file.writestr('%s.csv' % (data_set.name), data_set_file(request, data_set).body, compress_type=ZIP_DEFLATED)
    zip_file.close()
    return experiment
    
@view_config(route_name='survey.export')
@view_config(route_name='survey.export.ext')
def export(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            experiment = export_experiment(request, survey)
            return Response(experiment.getvalue(),
                            headers={'Content-Type': 'application/x-experiment',
                                     'Content-Disposition': 'attachment; filename=%s.exp' % (survey.title.replace(' ', '_').encode('utf-8'))})
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
