# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
try:
    import cPickle as pickle
except:
    import pickle
import transaction

from formencode import Schema, validators, api
from lxml import etree
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pywebtools.auth import is_authorised

from pyquest import helpers
from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey)
from pyquest.renderer import render
from pyquest.validation import XmlValidator

class SurveySchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    summary = validators.UnicodeString()
    content = XmlValidator('<pq:survey xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:survey>')
    schema = XmlValidator('<pq:survey xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:survey>', strip_wrapper=False)
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()

class SurveyStatusSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    status = validators.OneOf(['develop', 'testing', 'running', 'paused', 'finished'])

def create_schema(content):
    def process(element):
        if element.tag == '{http://paths.sheffield.ac.uk/pyquest}survey':
            return filter(lambda e: e, map(process, element))
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}single':
            if 'qsid' in element.attrib:
                qsheet = {'qsid': element.attrib['qsid'],
                          'type': 'single'}
                for child in element:
                    qsheet.update(process(child))
                return qsheet
            else:
                return {}
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}repeat':
            if 'qsid' in element.attrib:
                qsheet = {'qsid': element.attrib['qsid'],
                          'type': 'repeat'}
                for child in element:
                    qsheet.update(process(child))
                return qsheet
            else:
                return {}
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}finish':
            if 'qsid' in element.attrib:
                return {'qsid': element.attrib['qsid'],
                        'type': 'finish'}
            else:
                return {}
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}source':
            source = {'source': {'data_items': 1, 'control_items': 0}}
            for child in element:
                source['source'].update(process(child))
            return source
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}data_items':
            if 'count' in element.attrib:
                try:
                    return {'data_items': int(element.attrib['count'])}
                except ValueError:
                    return {'data_items': 1}
            else:
                return {'data_items': 1}
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}control_items':
            if 'count' in element.attrib:
                try:
                    return {'control_items': int(element.attrib['count'])}
                except ValueError:
                    return {'control_items': 0}
            else:
                return {'control_items': 0}
        else:
            return {}
    def link_qsheets(schema):
        for idx, instr in enumerate(schema):
            if (idx + 1) < len(schema):
                instr['next_qsid'] = schema[idx + 1]['qsid']
            else:
                instr['next_qsid'] = None
        return schema
    if content:
        return link_qsheets(process(etree.fromstring(content)))
    else:
        return []

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
                if 'content' in request.POST:
                    request.POST['schema'] = request.POST['content']
                params = SurveySchema().to_python(request.POST)
                check_csrf_token(request, params)
                with transaction.manager:
                    survey.title = params['title']
                    survey.summary = params['summary']
                    survey.content = params['content']
                    survey.schema = pickle.dumps(create_schema(params['schema']))
                    survey.styles = params['styles']
                    survey.scripts = params['scripts']
                    survey.status = 'develop'
                    survey.owned_by = user.id
                    dbsession.add(survey)
                    dbsession.flush()
                    sid = survey.id
                request.session.flash('Survey created', 'info')
                raise HTTPFound(request.route_url('survey.edit', sid=sid))
            except api.Invalid as e:
                e.params = request.POST
                return {'survey': survey,
                        'e': e}
        else:
            return {'survey': survey}
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
                    if 'content' in request.POST:
                        request.POST['schema'] = request.POST['content']
                    params = SurveySchema().to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        survey.title = params['title']
                        survey.summary = params['summary']
                        survey.content = params['content']
                        survey.schema = pickle.dumps(create_schema(params['schema']))
                        survey.styles = params['styles']
                        survey.scripts = params['scripts']
                        dbsession.add(survey)
                    request.session.flash('Survey updated', 'info')
                    raise HTTPFound(request.route_url('survey.edit',
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
            example = {'did': 0}
            if survey.data_items:
                example['did'] = survey.data_items[0].id
                for attr in survey.data_items[0].attributes:
                    example[attr.key] = attr.value
            return {'survey': survey,
                    'example': example}
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
                            for data_item in survey.data_items:
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
