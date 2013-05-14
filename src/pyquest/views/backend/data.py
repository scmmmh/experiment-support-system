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

from pyquest.helpers.data import create_data_item_sets
from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, DataItem,
                            DataItemAttribute, Question, DataItemControlAnswer,
                            Participant, DataItemSet)
import re

class DataItemSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    control_ = validators.StringBool(if_missing=False)
    control_answer_question = foreach.ForEach(validators.Int())
    control_answer_answer = foreach.ForEach(validators.UnicodeString())

class DataItemSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.String()

@view_config(route_name='dataset.list')
@render({'text/html': 'backend/data/set_list.html'})
def list(request):
    dbsession = DBSession()
    user = current_user(request)
    create_data_item_sets(dbsession, user)
    dis = dbsession.query(DataItemSet).filter(DataItemSet.owned_by==user.id).all()
    return {'dis': dis}

@view_config(route_name='dataset.delete')
@render({'text/html': 'backend/data/set_delete.html'})
def dataset_delete(request):
    dbsession = DBSession()
    dis = dbsession.query(DataItemSet).filter(DataItemSet.id==request.matchdict['disid']).first()
    user = current_user(request)
    if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'dis': dis}):
        if request.method == 'POST':
            check_csrf_token(request, request.POST)
            with transaction.manager:
                dbsession.delete(dis)
            request.session.flash('Data Item Set deleted', 'info')
            raise HTTPFound(request.route_url('dataset.list'))
        else:
            return {'dis': dis}
    else:
        redirect_to_login(request)

@view_config(route_name='dataset.edit')
@render({'text/html': 'backend/data/set_edit.html'})
def set_edit(request):
    dbsession = DBSession()
    dis = dbsession.query(DataItemSet).filter(DataItemSet.id==request.matchdict['disid']).first()
    user = current_user(request)
    if dis:
        if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'dis': dis}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                validator = DataItemSetSchema()
                params = validator.to_python(request.POST)
                with transaction.manager:
                    dbsession.add(dis)
                    dis.name = params['name']
                    dbsession.flush()
                raise HTTPFound(request.route_url('dataset.list'))
            else:
                return {'dis': dis}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()



@view_config(route_name='dataset.upload')
@render({'text/html': 'backend/data/set_upload.html'})
def set_upload(request):
    dbsession = DBSession()
    user = current_user(request)
    if request.method == 'POST':
        check_csrf_token(request, request.POST)
        try:
            if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
            reader = csv.DictReader(request.POST['source_file'].file)
            order = 1
            with transaction.manager:
                dis = DataItemSet(name = request.POST['source_file'].filename, owned_by=user.id)
                dbsession.add(dis)
                try:
                    for item in reader:
                        # removed section that checked matching with previous data for qsheet
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
            raise HTTPFound(request.route_url('dataset.list'))
        except api.Invalid as e:
            e.params = {}
            return {'e': e}
    else:
        return {}

@view_config(route_name='survey.data')
@render({'text/html': 'backend/data/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    if request.query_string:
        disid = int(re.sub('^.*=', '', request.query_string))
        dis = dbsession.query(DataItemSet).filter(DataItemSet.id==disid).first()
    else:
        dis = None
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            items = dbsession.query(DataItem).filter(DataItem.qsheet_id==request.matchdict['qsid']).order_by(DataItem.order)
            pages = int(math.ceil(items.count() / 10.0))
            page = 1
            if 'page' in request.params:
                try:
                    page = int(request.params['page'])
                except:
                    page = 1
            items = items.offset((page - 1) * 10).limit(10)
            return {'survey': survey,
                    'dis': dis,
                    'qsheet': qsheet,
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
    dbs = DBSession
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                try:
                    if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                        raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
                    reader = csv.DictReader(request.POST['source_file'].file)
                    if len(qsheet.data_items) > 0:
                        order = dbsession.query(func.max(DataItem.order)).filter(DataItem.qsheet_id==qsheet.id).first()[0] + 1
                    else:
                        order = 1
                    with transaction.manager:
                        qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
                        dis = DataItemSet(name = request.POST['source_file'].filename)
                        dbsession.add(dis)
                        try:
                            for item in reader:
                                # removed section that checked matching with previous data for qsheet
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
#                    raise HTTPFound(request.route_url('survey.data', sid=request.matchdict['sid'], qsid=request.matchdict['qsid'], _query={'disid' : str(dis.id)}))
                    raise HTTPFound(request.route_url('survey.data.view', sid = request.matchdict['sid'], did = did))
                except api.Invalid as e:
                    e.params = {}
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

@view_config(route_name='survey.data.new')
@render({'text/html': 'backend/data/new.html'})
def new(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    dis = dbsession.query(DataItemSet).filter(DataItemSet.id==request.matchdict['disid']).first()
    user = current_user(request)
    if survey and dis:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
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
                        new_data_item = DataItem(data_item_set_id=dis.id,
                                                 control=params['control_'])
                        if len(dis.items) > 0:
                            new_data_item.order = dbsession.query(func.max(DataItem.order)).filter(DataItem.data_item_set_id==dis.id).first()[0] + 1
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
                    raise HTTPFound(request.route_url('survey.dataset.edit',
                                                      sid=request.matchdict['sid'],
                                                      disid=request.matchdict['disid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
#                            'qsheet': qsheet,
                            'data_item': data_item}
            else:
                return {'survey': survey,
 #                       'qsheet': qsheet,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data.view')
@render({'text/html': 'backend/qsheet/view.html'})
def view(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.qsheet_id==request.matchdict['qsid'],
                                                      DataItem.id==request.matchdict['did'])).first()
    user = current_user(request)
    if survey and qsheet and data_item:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            example = {'did' : 0}
            example['did'] = data_item.id
            for attr in data_item.attributes:
                example[attr.key] = attr.value
            return {'survey': survey,
                    'qsheet': qsheet,
                    'example': example,
                    'participant': Participant(id=-1)}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()


@view_config(route_name='data.edit')
@render({'text/html': 'backend/data/edit.html'})
def edit(request):
    dbsession = DBSession()
#    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
#    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
#    data_item = dbsession.query(DataItem).filter(and_(DataItem.qsheet_id==request.matchdict['qsid'],
#                                                      DataItem.id==request.matchdict['did'])).first()
    data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()

    user = current_user(request)
    if data_item:
        if is_authorised(':dis.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'dis': data_item.item_set}):
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
                        disid=data_item.data_item_set_id
                    request.session.flash('Data updated', 'info')
                    raise HTTPFound(request.route_url('dataset.edit',
                                                      disid=disid))

                except api.Invalid as e:
                    e.params = request.POST
                    return {'data_item': data_item}
            else:
                return {'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.delete')
@render({'text/html': 'backend/data/delete.html'})
def delete(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
#    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
#    data_item = dbsession.query(DataItem).filter(and_(DataItem.qsheet_id==request.matchdict['qsid'],
#                                                      DataItem.id==request.matchdict['did'])).first()
    data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()

    user = current_user(request)
    if survey and data_item:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                with transaction.manager:
                    dbsession.delete(data_item)
                request.session.flash('Data deleted', 'info')
                raise HTTPFound(request.route_url('survey.dataset.edit', sid=survey.id, did=data_item.data_item_set_id))
            else:
                return {'survey': survey,
#                        'qsheet': qsheet,
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
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                with transaction.manager:
                    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
                    qsheet.data_items = []
                    dbsession.add(qsheet)
                request.session.flash('All data deleted', 'info')
                raise HTTPFound(request.route_url('survey.dataset.edit', sid=request.matchdict['sid'], did=data_item.data_item_set_id))
            else:
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.data.download')
@render({'text/csv': ''})
def download(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            columns = []
            rows = []
            if qsheet.data_items:
                columns = ['id_', 'control_'] + [a.key.encode('utf-8') for a in qsheet.data_items[0].attributes]
                for data_item in qsheet.data_items:
                    row = dict([(a.key.encode('utf-8'), a.value.encode('utf-8')) for a in data_item.attributes])
                    row.update(dict([('id_', data_item.id), ('control_', data_item.control)]))
                    rows.append(row)
            return {'columns': columns,
                    'rows': rows}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
