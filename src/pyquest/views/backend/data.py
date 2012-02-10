# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2012

@author: mhall
'''
import csv
import math
import transaction

from formencode import Schema, validators, api
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_, func

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, DataItem, DataItemAttribute)
from pyquest.renderer import render

class DataItemSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    control = validators.StringBool(not_empty=True)

@view_config(route_name='survey.data')
@render({'text/html': 'backend/data/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            show = 'all'
            items = dbsession.query(DataItem)
            if 'show' in request.params:
                if request.params['show'] == 'data':
                    show = 'data'
                    items = items.filter(DataItem.control==False)
                elif request.params['show'] == 'control':
                    show = 'control'
                    items = items.filter(DataItem.control==True)
            pages = int(math.ceil(items.count() / 10.0))
            page = 1
            if 'page' in request.params:
                try:
                    page = int(request.params['page'])
                except:
                    page = 1
            items = items.offset((page - 1) * 10).limit(10)
            return {'survey': survey,
                    'show': show,
                    'items': items,
                    'page': page,
                    'pages': pages}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data.upload')
@render({'text/html': 'backend/data/upload.html'})
def upload(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                if 'csrf_token' not in request.POST or request.POST['csrf_token'] != request.session.get_csrf_token():
                    raise HTTPForbidden('Cross-site request forgery detected')
                try:
                    print request.POST['source_file'].__class__
                    if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                        raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
                    reader = csv.DictReader(request.POST['source_file'].file)
                    if len(survey.all_items) > 0:
                        order = dbsession.query(func.max(DataItem.order)).filter(DataItem.survey_id==survey.id).first()[0] + 1
                    else:
                        order = 1
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        try:
                            for item in reader:
                                if len(survey.all_items) > 0:
                                    keys = item.keys()
                                    for attribute in survey.all_items[0].attributes:
                                        if attribute.key not in item:
                                            raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Key "%s" missing from the uploaded data' % attribute.key})
                                        else:
                                            keys.remove(attribute.key)
                                    if len(keys) > 0:
                                        raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Extra key(s) "%s" found in the uploaded data' % ', '.join(keys)})
                                data_item = DataItem(order=order,
                                                     control=False)
                                if 'control' in item and item['control'] in ['true', 'True']:
                                    data_item.control = True
                                for idx, (key, value) in enumerate(item.items()):
                                    if key != 'control':
                                        data_item.attributes.append(DataItemAttribute(key=key.decode('utf-8'),
                                                                                      value=value.decode('utf-8'),
                                                                                      order=idx + 1))
                                survey.all_items.append(data_item)
                                dbsession.add(data_item)
                        except csv.Error:
                            raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'The file you selected is not a valid CSV file'})
                    request.session.flash('Data uplodated', 'info')
                    raise HTTPFound(request.route_url('survey.data', sid=request.matchdict['sid']))
                except api.Invalid as e:
                    e.params = {}
                    return {'survey': survey,
                            'e': e}
            else:
                return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data.new')
@render({'text/html': 'backend/data/new.html'})
def new(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if len(survey.all_items) > 0:
                data_item = survey.all_items[0]
            else:
                data_item = DataItem()
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute in data_item.attributes:
                        validator.add_field(attribute.key, validators.UnicodeString(not_empty=True))
                    params = validator.to_python(request.POST)
                    if params['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                    with transaction.manager:
                        new_data_item = DataItem(survey_id=survey.id,
                                                 control=params['control'])
                        if len(survey.all_items) > 0:
                            new_data_item.order = dbsession.query(func.max(DataItem.order)).filter(DataItem.survey_id==survey.id).first()[0] + 1
                        else:
                            new_data_item.order = 1
                        for attribute in data_item.attributes:
                            new_data_item.attributes.append(DataItemAttribute(key=attribute.key,
                                                                              value=params[attribute.key],
                                                                              order=attribute.order,
                                                                              answer=None))
                        dbsession.add(new_data_item)
                    request.session.flash('Data added', 'info')
                    raise HTTPFound(request.route_url('survey.data',
                                                      sid=request.matchdict['sid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'data_item': data_item}
            else:
                return {'survey': survey,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data.edit')
@render({'text/html': 'backend/data/edit.html'})
def edit(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.survey_id==request.matchdict['sid'],
                                                      DataItem.id==request.matchdict['did'])).first()
    user = current_user(request)
    if survey and data_item:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute in data_item.attributes:
                        validator.add_field(attribute.key, validators.UnicodeString(not_empty=True))
                    params = validator.to_python(request.POST)
                    if params['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                    with transaction.manager:
                        data_item.control = params['control']
                        for attribute in data_item.attributes:
                            attribute.value = params[attribute.key]
                        dbsession.add(data_item)
                    request.session.flash('Data updated', 'info')
                    raise HTTPFound(request.route_url('survey.data.edit',
                                                      sid=request.matchdict['sid'],
                                                      did=request.matchdict['did']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'data_item': data_item}
            else:
                return {'survey': survey,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data.delete')
@render({'text/html': 'backend/data/delete.html'})
def delete(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.survey_id==request.matchdict['sid'],
                                                      DataItem.id==request.matchdict['did'])).first()
    user = current_user(request)
    if survey and data_item:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                if 'csrf_token' not in request.POST or request.POST['csrf_token'] != request.session.get_csrf_token():
                    raise HTTPForbidden('Cross-site request forgery detected')
                with transaction.manager:
                    dbsession.delete(data_item)
                request.session.flash('Data deleted', 'info')
                raise HTTPFound(request.route_url('survey.data', sid=survey.id))
            else:
                return {'survey': survey,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data.clear')
@render({'text/html': 'backend/data/clear.html'})
def clear(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if request.method == 'POST':
                if 'csrf_token' not in request.POST or request.POST['csrf_token'] != request.session.get_csrf_token():
                    raise HTTPForbidden('Cross-site request forgery detected')
                with transaction.manager:
                    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                    survey.all_items = []
                    dbsession.add(survey)
                request.session.flash('All data deleted', 'info')
                raise HTTPFound(request.route_url('survey.data', sid=request.matchdict['sid']))
            else:
                return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
            