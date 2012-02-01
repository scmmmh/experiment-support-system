# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
import transaction

from formencode import Schema, validators, api, variabledecode
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey)
from pyquest.renderer import render

class SurveySchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    
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
                    params = SurveySchema().to_python(request.POST)
                    if params['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                    with transaction.manager:
                        survey.title = params['title']
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
            example = {'did': -1}
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
