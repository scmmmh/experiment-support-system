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
from pywebtools.auth import is_authorised
from pywebtools.renderer import render
from sqlalchemy import and_, func, null

from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, DataItem,
                            DataItemAttribute, Question, DataItemControlAnswer,
                            Participant, DataSet)
import re

class DataItemSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    control_ = validators.StringBool(if_missing=False)
    control_answer_question = foreach.ForEach(validators.Int())
    control_answer_answer = foreach.ForEach(validators.UnicodeString())

class DataSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.String()

class NewDataSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.String()
    item_attributes = foreach.ForEach(validators.UnicodeString())

@view_config(route_name='data.list')
@render({'text/html': 'backend/data/set_list.html'})
def list_datasets(request):
    dbsession = DBSession()
    user = current_user(request)
    dis = dbsession.query(DataSet).filter(and_(DataSet.owned_by==user.id, DataSet.survey_id==request.matchdict['sid'])).all()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    return {'survey': survey,
            'dis': dis}

@view_config(route_name='data.view')
@render({'text/html': 'backend/data/set_view.html'})
def dataset_view(request):
    dbsession = DBSession()
    dis = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    return {'survey': survey, 
            'dis': dis}

@view_config(route_name='data.attach')
@render({'text/html': 'backend/data/set_attach.html'})
def dataset_attach(request):
    dbsession = DBSession()
    user = current_user(request)
    qs = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    survey = dbsession.query(Survey).filter(Survey.id==qs.survey_id).first()
    dsoptions = create_ds_options(dbsession, user, survey)
    if request.method == 'POST':
        sid = qs.survey_id
        qsid = qs.id
        if request.params['dsid'] != '0':
            check_csrf_token(request, request.POST)
            with transaction.manager:
                dbsession.add(qs)
                qs.dataset_id = request.params['dsid']
                dbsession.flush()
            request.session.flash('DataSet attached', 'info')
        raise HTTPFound(request.route_url('survey.data', sid=sid, qsid=qsid))
    else:
        return {'dsid' : 0,
                'dsoptions' : dsoptions,
                's' : survey,
                'qs' : qs}

@view_config(route_name='data.detach')
@render({'text/html': 'backend/data/set_detach.html'})
def dataset_detach(request):
    dbsession = DBSession()
    ds = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    qs = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    if request.method == 'POST':
            check_csrf_token(request, request.POST)
            with transaction.manager:
                dbsession.add(qs)
                qs.data_set = None
                dbsession.flush()
                sid = qs.survey_id
            request.session.flash('DataSet detached', 'info')
            raise HTTPFound(request.route_url('survey.view', sid=sid))
    else:
        return {'ds' : ds,
                'qs' : qs}

@view_config(route_name='data.new')
@render({'text/html': 'backend/data/set_new.html'})
def dataset_new(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    dis = DataSet()
    if request.method == 'POST':
        try:
            check_csrf_token(request, request.POST)
            validator = NewDataSetSchema()
            params = validator.to_python(request.POST)
            with transaction.manager:
                dis.name = params['name']
                dis.owned_by = user.id
                dis.survey_id = survey.id
                data_item = DataItem(order=1)
                for idx, key in enumerate(params['item_attributes']):
                    data_item.attributes.append(DataItemAttribute(key=key.decode('utf-8'), order=idx+1))
                dis.items.append(data_item)
                dbsession.add(dis)
                dbsession.flush()
                dsid = dis.id
            request.session.flash('DataSet created', 'info')
            raise HTTPFound(request.route_url('data.edit', sid=request.matchdict['sid'], dsid=dsid))
        except api.Invalid as e:
            e.params = request.POST
            return {'survey': survey,
                    'dis': dis,
                    'e': e}
    else:
        return {'survey': survey,
                'dis': dis}

@view_config(route_name='data.delete')
@render({'text/html': 'backend/data/set_delete.html'})
def dataset_delete(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    dis = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    user = current_user(request)
    if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'dis': dis}):
        if request.method == 'POST':
            check_csrf_token(request, request.POST)
            with transaction.manager:
                sid = dis.survey_id
                dbsession.delete(dis)
            request.session.flash('Data Item Set deleted', 'info')
            raise HTTPFound(request.route_url('data.list', sid=sid))
        else:
            return {'survey': survey,
                    'dis': dis}
    else:
        redirect_to_login(request)

@view_config(route_name='data.edit')
@render({'text/html': 'backend/data/set_edit.html'})
def dataset_edit(request):
    dbsession = DBSession()
    dis = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if dis:
        if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'dis': dis}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                validator = NewDataSetSchema()
                params = validator.to_python(request.POST)
                with transaction.manager:
                    dbsession.add(dis)
                    dis.name = params['name']
                    sid = dis.survey_id
                    for item in dis.items:
                        for idx, key in enumerate(params['item_attributes']):
                            for attribute in item.attributes:
                                if (attribute.order == idx +1):
                                    attribute.key = key.decode('utf-8')
                    dbsession.flush()
                raise HTTPFound(request.route_url('data.list', sid=sid))
            else:
                return {'survey': survey,
                        'dis': dis}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()



@view_config(route_name='data.upload')
@render({'text/html': 'backend/data/set_upload.html'})
def dataset_upload(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if request.method == 'POST':
        check_csrf_token(request, request.POST)
        try:
            if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
            reader = csv.DictReader(request.POST['source_file'].file)
            order = 1
            with transaction.manager:
                dis = DataSet(name = request.POST['source_file'].filename, owned_by=user.id, survey_id=survey.id)
                dbsession.add(dis)
                try:
                    for item in reader:
                        data_item = DataItem(order=order)
                        if 'control_' in item:
                            data_item.control = validators.StringBool().to_python(item['control_'])
                        for idx, (key, value) in enumerate(item.items()):
                            if key != 'control_':
                                data_item.attributes.append(DataItemAttribute(key=key.decode('utf-8'),
                                                                              value=value.decode('utf-8') if value else u'',
                                                                              order=idx + 1))
                                dis.items.append(data_item)
                except csv.Error:
                    raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'The file you selected is not a valid CSV file'})
                dbsession.flush()
                did = dis.id
            request.session.flash('Data uploaded', 'info')
            raise HTTPFound(request.route_url('data.list', sid=request.matchdict['sid']))
        except api.Invalid as e:
            e.params = {}
            return {'e': e}
    else:
        return {'survey': survey}

@view_config(route_name='data.download')
@render({'text/csv': ''})
def dataset_download(request):
    dbsession = DBSession()
    dis = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    user = current_user(request)
    if dis:
        if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'dis': dis}):
            columns = []
            rows = []
            if len(dis.items) > 0:
                columns = ['id_', 'control_'] + [a.key.encode('utf-8') for a in dis.items[0].attributes]
                for item in dis.items:
                    row = dict([(a.key.encode('utf-8'), a.value.encode('utf-8')) for a in item.attributes])
                    row.update(dict([('id_', item.id), ('control_', item.control)]))
                    rows.append(row)
            return {'columns': columns,
                    'rows': rows}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data')
@render({'text/html': 'backend/data/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    dis = dbsession.query(DataSet).filter(DataSet.id==qsheet.dataset_id).first()
    return {'dis': dis,
            'qs': qsheet,
            's': survey}

@view_config(route_name='data.item.new')
@render({'text/html': 'backend/data/item_new.html'})
def new(request):
    dbsession = DBSession()
    dis = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if dis:
        if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'dis': dis}):
            if len(dis.items) > 0:
                data_item = dis.items[0]
            else:
                data_item = DataItem()
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute in data_item.attributes:
                        validator.add_field(attribute.key, validators.UnicodeString())
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        new_data_item = DataItem(dataset_id=dis.id,
                                                 control=params['control_'])
                        if len(dis.items) > 0:
                            new_data_item.order = dbsession.query(func.max(DataItem.order)).filter(DataItem.dataset_id==dis.id).first()[0] + 1
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
                    raise HTTPFound(request.route_url('data.edit', sid=dis.survey_id, dsid=request.matchdict['dsid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'dis': dis,
                            'data_item': data_item}
            else:
                return {'survey': survey,
                        'dis': dis,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.item.edit')
@render({'text/html': 'backend/data/item_edit.html'})
def edit(request):
    dbsession = DBSession()
    data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    dis = dbsession.query(DataSet).filter(DataSet.id==data_item.dataset_id).first()
    user = current_user(request)
    if data_item:
        if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'dis': data_item.data_set}):
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute in data_item.attributes:
                        validator.add_field(attribute.key, validators.UnicodeString(not_empty=True))
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()
                        data_item.control = params['control_']
                        for attribute in data_item.attributes:
                            attribute.value = params[attribute.key]
                        data_item.control_answers = []
                        for idx in range(0, min(len(params['control_answer_question']), len(params['control_answer_answer']))):
                            question = dbsession.query(Question).filter(Question.id==params['control_answer_question'][idx]).first()
                            if question and params['control_answer_answer'][idx].strip() != '':
                                data_item.control_answers.append(DataItemControlAnswer(question=question, answer=params['control_answer_answer'][idx]))
                        dbsession.add(data_item)
                        dsid = data_item.dataset_id
                        sid = data_item.data_set.survey_id
                    request.session.flash('Data updated', 'info')
                    raise HTTPFound(request.route_url('data.edit', sid=sid, dsid=dsid))

                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'dis': dis,
                            'data_item': data_item}
            else:
                return {'survey': survey,
                        'dis':dis,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.item.delete')
@render({'text/html': 'backend/data/item_delete.html'})
def delete(request):
    dbsession = DBSession()
    data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()
    dis = dbsession.query(DataSet).filter(DataSet.id==data_item.dataset_id).first()
    user = current_user(request)
    if dis and data_item:
        if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'dis': dis}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                dbsession.add(data_item)
                sid = data_item.data_set.survey_id
                dsid = data_item.dataset_id
                with transaction.manager:
                    dbsession.delete(data_item)
                request.session.flash('Data deleted', 'info')
                raise HTTPFound(request.route_url('data.edit', sid=sid, dsid=dsid))
            else:
                return {'dis': dis,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def create_ds_options(dbsession, user, survey):
    """Creates a list of tuples representing all the available DataSets. The list is suitable for use in a select item.
    
    :param dbsession: the DataBase session
    :param user: the current user
    :return a list of tuples for use in select items representing the available DataSets
    """
    ds_options = []
    for d in dbsession.query(DataSet).filter(and_(DataSet.owned_by==user.id, DataSet.survey_id==survey.id)).all():
        ds_options.append((d.id, d.name))

    return ds_options;
