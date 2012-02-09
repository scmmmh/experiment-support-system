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

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey)
from pyquest.renderer import render
from pyquest.validation import XmlValidator

class SurveySchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    content = XmlValidator('<pq:survey xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:survey>')
    schema = XmlValidator('<pq:survey xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:survey>', strip_wrapper=False)

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
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}data_items':
            data_items = {'data_items': {'data': {'count': 1}}}
            for child in element:
                data_items['data_items'].update(process(child))
            return data_items
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}data':
            if 'count' in element.attrib:
                try:
                    return {'data': {'count': int(element.attrib['count'])}}
                except ValueError:
                    return {'data': {'count': 1}}
            return {'data': {'count': 1}}
        elif element.tag == '{http://paths.sheffield.ac.uk/pyquest}control':
            if 'count' in element.attrib:
                try:
                    return {'control': {'count': int(element.attrib['count'])}}
                except ValueError:
                    return {'control': {'count': 1}}
            return {'control': {'count': 1}}
    def link_qsheets(schema):
        for idx, instr in enumerate(schema):
            if instr['type'] == 'single':
                if (idx + 1) < len(schema):
                    instr['next_qsid'] = schema[idx + 1]['qsid']
                else:
                    instr['next_qsid'] = None
            elif instr['type'] == 'repeat':
                instr['next_qsid'] = instr['qsid']
        return schema
    return link_qsheets(process(etree.fromstring(content)))

@view_config(route_name='survey')
@render({'text/html': 'backend/index.html'})
def index(request):
    user = current_user(request)
    if user:
        return {'surveys': user.surveys}
    else:
        redirect_to_login(request)

@view_config(route_name='survey.overview')
@render({'text/html': 'backend/overview.html'})
def overview(request):
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
    
@view_config(route_name='survey.edit')
@render({'text/html': 'backend/edit.html'})
def edit(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                try:
                    if 'content' in request.POST:
                        request.POST['schema'] = request.POST['content']
                    params = SurveySchema().to_python(request.POST)
                    if params['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                    with transaction.manager:
                        survey.title = params['title']
                        survey.content = params['content']
                        survey.schema = pickle.dumps(create_schema(params['schema']))
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

@view_config(route_name='survey.preview')
@render({'text/html': 'backend/preview.html'})
def preview(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            example = {'did': 0}
            if survey.all_items:
                example['did'] = survey.all_items[0].id
                for attr in survey.all_items[0].attributes:
                    example[attr.key] = attr.value
            return {'survey': survey,
                    'example': example}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
