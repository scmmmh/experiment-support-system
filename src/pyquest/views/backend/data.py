# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2012

@author: mhall
'''
import csv
import math
import transaction

from formencode import Schema, validators, api, foreach
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_, func
from pywebtools.auth import is_authorised

from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, DataItem, DataItemAttribute,
    Question, DataItemControlAnswer)
from pyquest.renderer import render

class DataItemSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    control_ = validators.StringBool(if_missing=False)
    control_answer_question = foreach.ForEach(validators.Int())
    control_answer_answer = foreach.ForEach(validators.UnicodeString())

@view_config(route_name='survey.data')
@render({'text/html': 'backend/data/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            items = dbsession.query(DataItem).filter(DataItem.survey_id==request.matchdict['sid']).order_by(DataItem.id)
            pages = int(math.ceil(items.count() / 10.0))
            page = 1
            if 'page' in request.params:
                try:
                    page = int(request.params['page'])
                except:
                    page = 1
            items = items.offset((page - 1) * 10).limit(10)
            return {'survey': survey,
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
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                try:
                    if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                        raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
                    reader = csv.DictReader(request.POST['source_file'].file)
                    if len(survey.data_items) > 0:
                        order = dbsession.query(func.max(DataItem.order)).filter(DataItem.survey_id==survey.id).first()[0] + 1
                    else:
                        order = 1
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        try:
                            for item in reader:
                                if len(survey.data_items) > 0:
                                    keys = item.keys()
                                    if 'control_' in keys:
                                        keys.remove('control_')
                                    for attribute in survey.data_items[0].attributes:
                                        if attribute.key not in item:
                                            raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Key "%s" missing from the uploaded data' % attribute.key})
                                        else:
                                            keys.remove(attribute.key)
                                    if len(keys) > 0:
                                        raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Extra key(s) "%s" found in the uploaded data' % ', '.join(keys)})
                                data_item = DataItem(order=order)
                                if 'control_' in item:
                                    data_item.control = validators.StringBool().to_python(item['control_'])
                                for idx, (key, value) in enumerate(item.items()):
                                    if key != 'control_':
                                        data_item.attributes.append(DataItemAttribute(key=key.decode('utf-8'),
                                                                                      value=value.decode('utf-8'),
                                                                                      order=idx + 1))
                                survey.data_items.append(data_item)
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
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if len(survey.data_items) > 0:
                data_item = survey.data_items[0]
            else:
                data_item = DataItem()
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute in data_item.attributes:
                        validator.add_field(attribute.key, validators.UnicodeString(not_empty=True))
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        new_data_item = DataItem(survey_id=survey.id,
                                                 control=params['control_'])
                        if len(survey.data_items) > 0:
                            new_data_item.order = dbsession.query(func.max(DataItem.order)).filter(DataItem.survey_id==survey.id).first()[0] + 1
                        else:
                            new_data_item.order = 1
                        for attribute in data_item.attributes:
                            new_data_item.attributes.append(DataItemAttribute(key=attribute.key,
                                                                              value=params[attribute.key],
                                                                              order=attribute.order))
                        for idx in range(0, min(len(params['control_answer_question']), len(params['control_answer_answer']))):
                            question = dbsession.query(Question).filter(Question.id==params['control_answer_question'][idx]).first()
                            if question and params['control_answer_answer'][idx].strip() != '':
                                new_data_item.control_answers.append(DataItemControlAnswer(question=question, answer=params['control_answer_answer'][idx]))
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
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute in data_item.attributes:
                        validator.add_field(attribute.key, validators.UnicodeString(not_empty=True))
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        data_item = dbsession.query(DataItem).filter(and_(DataItem.survey_id==request.matchdict['sid'],
                                                                          DataItem.id==request.matchdict['did'])).first()
                        data_item.control = params['control_']
                        for attribute in data_item.attributes:
                            attribute.value = params[attribute.key]
                        data_item.control_answers = []
                        for idx in range(0, min(len(params['control_answer_question']), len(params['control_answer_answer']))):
                            question = dbsession.query(Question).filter(Question.id==params['control_answer_question'][idx]).first()
                            if question and params['control_answer_answer'][idx].strip() != '':
                                data_item.control_answers.append(DataItemControlAnswer(question=question, answer=params['control_answer_answer'][idx]))
                        dbsession.add(data_item)
                    request.session.flash('Data updated', 'info')
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

@view_config(route_name='survey.data.delete')
@render({'text/html': 'backend/data/delete.html'})
def delete(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.survey_id==request.matchdict['sid'],
                                                      DataItem.id==request.matchdict['did'])).first()
    user = current_user(request)
    if survey and data_item:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
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
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                with transaction.manager:
                    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                    survey.data_items = []
                    dbsession.add(survey)
                request.session.flash('All data deleted', 'info')
                raise HTTPFound(request.route_url('survey.data', sid=request.matchdict['sid']))
            else:
                return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
            