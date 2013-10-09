# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2012

@author: mhall
'''
import csv
import itertools
import json
import transaction

from formencode import Schema, validators, api, variabledecode, foreach
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pywebtools.auth import is_authorised
from pywebtools.renderer import render

from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, DataItem,
                            DataItemAttribute, Question, DataItemControlAnswer,
                            DataSet, DataSetAttributeKey, PermutationSet,
                            DataSetRelation)

class DataItemSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    control_ = validators.StringBool(if_missing=False)
    control_answer_question = foreach.ForEach(validators.Int())
    control_answer_answer = foreach.ForEach(validators.UnicodeString())

class DataSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.String()

class DataSetAttributeKeySchema(Schema):
    key = validators.UnicodeString()
    id = validators.Int(if_missing=0)

class NewDataSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.String()

    pre_validators = [variabledecode.NestedVariables()]

class EditDataSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.String()
    attribute_keys = foreach.ForEach(DataSetAttributeKeySchema())

    pre_validators = [variabledecode.NestedVariables()]

class AttachDataSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    dsid = validators.Int()
    
class NewPermutationSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString()

class EditPermutationSetSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString()
    tasks = validators.Int()
    tasks_mode = validators.UnicodeString()
    interfaces = validators.Int()
    interfaces_mode = validators.UnicodeString()

@view_config(route_name='data.list')
@render({'text/html': 'backend/data/list.html'})
def dataset_list(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
        return {'survey': survey}
    else:
        redirect_to_login(request)

@view_config(route_name='data.view')
@render({'text/html': 'backend/data/view.html'})
def dataset_view(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            data_set = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
            if data_set:
                return {'survey': survey, 
                        'data_set': data_set}
            else:
                raise HTTPNotFound()
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.new')
@render({'text/html': 'backend/data/dataset_new.html'})
def dataset_new(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    params = NewDataSetSchema().to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        data_set = DataSet(name=params['name'], owned_by=user.id, survey_id=survey.id)
                        dbsession.add(data_set)
                        dbsession.flush()
                        dsid = data_set.id
                    request.session.flash('Data Set created', 'info')
                    raise HTTPFound(request.route_url('data.edit', sid=request.matchdict['sid'], dsid=dsid))
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

def load_csv_file(file_data, file_name, survey, dbsession):
    reader = csv.DictReader(file_data)
    count = 1
    offset = 0
    data_set = DataSet(name = file_name, survey_id=survey.id)
    dbsession.add(data_set)
    try:
        for item in reader:
            data_item = DataItem(order=count)
            if 'control_' in item:
                data_item.control = validators.StringBool().to_python(item['control_'])
                offset = 1
            order = 1
            for idx, (key, value) in enumerate(item.items()):
                if key != 'control_':
                    if count == 1:
                        attribute_key = DataSetAttributeKey(key=key.decode('utf-8'), order=order)
                        order = order + 1
                        data_set.attribute_keys.append(attribute_key)
                        dbsession.flush()
                    else:
                        attribute_key = data_set.attribute_keys[idx - offset]
                    data_item.attributes.append(DataItemAttribute(value=value.decode('utf-8') if value else u'', key_id=attribute_key.id))
                    data_set.items.append(data_item)
            count = count + 1
    except csv.Error:
        raise api.Invalid('Invalid CSV file', {}, None, error_dict={'source_file': 'The file you selected is not a valid CSV file'})
    return data_set

@view_config(route_name='data.upload')
@render({'text/html': 'backend/data/dataset_upload.html'})
def dataset_upload(request):
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
                    with transaction.manager:
                        data_set = load_csv_file(request.POST['source_file'].file, request.POST['source_file'].filename, survey, dbsession).id
                        dbsession.flush()
                        dsid = data_set.id
                    request.session.flash('Data uploaded', 'info')
                    raise HTTPFound(request.route_url('data.view', sid=request.matchdict['sid'], dsid=dsid))
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

@view_config(route_name='data.edit')
@render({'text/html': 'backend/data/dataset_edit.html'})
def dataset_edit(request):
    dbsession = DBSession()
    data_set = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey and data_set:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                params = EditDataSetSchema().to_python(request.POST)
                check_csrf_token(request, request.params)
                with transaction.manager:
                    dbsession.add(data_set)
                    data_set.name = params['name']
                    new_ids = []
                    for attribute_key_param in params['attribute_keys']:
                        new_ids.append(attribute_key_param['id'])
                    for old_attribute_key in data_set.attribute_keys:
                        if old_attribute_key.id not in new_ids:
                            data_set.attribute_keys.remove(old_attribute_key)
                            dbsession.delete(old_attribute_key)
                    for order, attribute_key_param in enumerate(params['attribute_keys']):
                        if attribute_key_param['id'] == None:
                            attribute_key = DataSetAttributeKey(key=attribute_key_param['key'], order=order)
                            data_set.attribute_keys.append(attribute_key)
                            for item in data_set.items:
                                item.attributes.append(DataItemAttribute(key_id=attribute_key.id))
                        else:
                            attribute_key = dbsession.query(DataSetAttributeKey).filter(DataSetAttributeKey.id==attribute_key_param['id']).first()
                            attribute_key.key = attribute_key_param['key']
                            attribute_key.order = order
                raise HTTPFound(request.route_url('data.view', sid=request.matchdict['sid'], dsid=request.matchdict['dsid']))
            else:
                return {'survey': survey,
                        'data_set': data_set}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.delete')
@render({'text/html': 'backend/data/dataset_delete.html'})
def dataset_delete(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_set = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    if survey and data_set:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                with transaction.manager:
                    dbsession.delete(data_set)
                request.session.flash('Data Set deleted', 'info')
                raise HTTPFound(request.route_url('data.list', sid=request.matchdict['sid']))
            else:
                return {'survey': survey,
                        'data_set': data_set}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.download')
@render({'text/csv': ''})
def dataset_download(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_set = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    if survey and data_set:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            columns = []
            rows = []
            if len(data_set.items) > 0:
                columns = ['id_', 'control_'] + [a.key.key.encode('utf-8') for a in data_set.items[0].attributes]
                for item in data_set.items:
                    row = dict([(a.key.key.encode('utf-8'), a.value.encode('utf-8')) for a in item.attributes])
                    row.update(dict([('id_', item.id), ('control_', item.control)]))
                    rows.append(row)
            return {'columns': columns,
                    'rows': rows}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.item.new')
@render({'text/html': 'backend/data/item_new.html'})
def item_new(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_set = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    if survey and data_set:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute in data_set.attribute_keys:
                        validator.add_field(attribute.key, validators.UnicodeString())
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        dbsession.add(data_set)
                        new_data_item = DataItem(dataset_id=data_set.id,
                                                 control=params['control_'])
                        for attribute_key in data_set.attribute_keys:
                            new_data_item.attributes.append(DataItemAttribute(value=params[attribute_key.key],
                                                                              key_id=attribute_key.id))
                        for idx in range(0, min(len(params['control_answer_question']), len(params['control_answer_answer']))):
                            question = dbsession.query(Question).filter(Question.id==params['control_answer_question'][idx]).first()
                            if question and params['control_answer_answer'][idx].strip() != '':
                                new_data_item.control_answers.append(DataItemControlAnswer(question=question, answer=params['control_answer_answer'][idx]))
                        dbsession.add(new_data_item)
                    request.session.flash('Data added', 'info')
                    raise HTTPFound(request.route_url('data.view', sid=request.matchdict['sid'], dsid=request.matchdict['dsid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'data_set': data_set}
            else:
                return {'survey': survey,
                        'data_set': data_set}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.item.edit')
@render({'text/html': 'backend/data/item_edit.html'})
def edit(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_set = dbsession.query(DataSet).filter(DataSet.id==request.matchdict['dsid']).first()
    data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()
    if survey and data_set and data_item:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    validator = DataItemSchema()
                    for attribute_key in data_set.attribute_keys:
                        validator.add_field(attribute_key.key, validators.UnicodeString(not_empty=True))
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()
                        data_item.control = params['control_']
                        for attribute in data_item.attributes:
                            attribute.value = params[attribute.key.key]
                        data_item.control_answers = []
                        for idx in range(0, min(len(params['control_answer_question']), len(params['control_answer_answer']))):
                            question = dbsession.query(Question).filter(Question.id==params['control_answer_question'][idx]).first()
                            if question and params['control_answer_answer'][idx].strip() != '':
                                data_item.control_answers.append(DataItemControlAnswer(question=question, answer=params['control_answer_answer'][idx]))
                        dbsession.add(data_item)
                        dsid = data_item.dataset_id
                        sid = data_item.data_set.survey_id
                    request.session.flash('Data updated', 'info')
                    raise HTTPFound(request.route_url('data.view', sid=sid, dsid=dsid))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'data_set': data_set,
                            'data_item': data_item}
            else:
                return {'survey': survey,
                        'data_set':data_set,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.item.delete')
@render({'text/html': 'backend/data/item_delete.html'})
def delete(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    data_item = dbsession.query(DataItem).filter(DataItem.id==request.matchdict['did']).first()
    data_set = dbsession.query(DataSet).filter(DataSet.id==data_item.dataset_id).first()
    if survey and data_set and data_item:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                with transaction.manager:
                    dbsession.delete(data_item)
                request.session.flash('Data deleted', 'info')
                raise HTTPFound(request.route_url('data.view', sid=request.matchdict['sid'], dsid=request.matchdict['dsid']))
            else:
                return {'survey': survey,
                        'data_set': data_set,
                        'data_item': data_item}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='data.new.permset')
@render({'text/html': 'backend/data/permset_new.html'})
def permset_new(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    params = NewPermutationSetSchema().to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        permset = PermutationSet(name=params['name'], owned_by=user.id, survey_id=survey.id)
                        dbsession.add(permset)
                        rel = DataSetRelation(subject=permset, rel='tasks')
                        rel.data = {'mode': 'within'}
                        rel = DataSetRelation(subject=permset, rel='interfaces')
                        rel.data = {'mode': 'within'}
                        DataSetAttributeKey(dataset=permset, key='permutation', order=0)
                        dbsession.flush()
                        permset_id = permset.id
                    request.session.flash('Permutation set created', 'info')
                    raise HTTPFound(request.route_url('data.edit.permset', sid=request.matchdict['sid'], dsid=permset_id))
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

@view_config(route_name='data.edit.permset')
@render({'text/html': 'backend/data/permset_edit.html'}) # TODO: Fix permutation generation
def permset_edit(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    permset = dbsession.query(PermutationSet).filter(PermutationSet.id==request.matchdict['dsid']).first()
    if request.method == 'POST':
        try:
            check_csrf_token(request, request.POST)
            validator = EditPermutationSetSchema()
            params = validator.to_python(request.POST)
            with transaction.manager:
                dbsession.add(permset)

                permset.name = params['name']
                permset.items = []
                permset.tasks.object_id = params['tasks']
                permset.tasks.data = {'mode': params['tasks_mode']}
                permset.interfaces.object_id = params['interfaces']
                permset.interfaces.data = {'mode': params['interfaces_mode']}
                
                task_items = [dict([(attr.key.key, attr.value) for attr in d.attributes]) for d in dbsession.query(DataItem).filter(DataItem.dataset_id==params['tasks'])]
                interface_items = [dict([(attr.key.key, attr.value) for attr in d.attributes]) for d in dbsession.query(DataItem).filter(DataItem.dataset_id==params['interfaces'])]
                permutations = []
                if task_items and interface_items:
                    if params['tasks_mode'] == 'within':
                        if params['interfaces_mode'] == 'within':
                            permutations = itertools.permutations(itertools.product(task_items, interface_items))
                        else:
                            for interface in interface_items:
                                permutations.extend(itertools.permutations(itertools.product(task_items, [interface])))
                    else:
                        if params['interfaces_mode'] == 'within':
                            for task in task_items:
                                permutations.extend(itertools.permutations(itertools.product([task], interface_items)))
                        else:
                            permutations = itertools.product(task_items, interface_items)
                for comb in permutations:
                    di = DataItem()
                    value = []
                    for pair in comb:
                        data = {}
                        data.update(pair[0])
                        data.update(pair[1])
                        value.append(data)
                    di.attributes.append(DataItemAttribute(key_id=permset.attribute_keys[0].id,
                                                           value=json.dumps(value)))
                    permset.items.append(di)
            request.session.flash('PermutationSet updated', 'info')
            raise HTTPFound(request.route_url('data.view', sid=request.matchdict['sid'], dsid=request.matchdict['dsid']))
        except api.Invalid as e:
            dbsession.add(survey)
            e.params = request.POST
            return {'survey': survey,
                    'permset': permset}
    else:
        return {'survey': survey,
                'permset': permset}

@view_config(route_name='data.edit.permset.count')
@render({'application/json': True})
def permset_count(request):
    try:
        dbsession = DBSession()
        validator = EditPermutationSetSchema()
        params = validator.to_python(request.POST)
        task_items = [d.attributes[0].value for d in dbsession.query(DataItem).filter(DataItem.dataset_id==params['tasks'])]
        interface_items = [d.attributes[0].value for d in dbsession.query(DataItem).filter(DataItem.dataset_id==params['interfaces'])]
        if task_items and interface_items:
            count = 0
            if params['tasks_mode'] == 'within':
                if params['interfaces_mode'] == 'within':
                    for _ in itertools.permutations(itertools.product(task_items, interface_items)):
                        count = count + 1
                        if count > 20000:
                            break
                else:
                    for interface in interface_items:
                        for _ in itertools.permutations(itertools.product(task_items, [interface])):
                            count = count + 1
                            if count > 20000:
                                break
            else:
                if params['interfaces_mode'] == 'within':
                    for task in task_items:
                        for _ in itertools.permutations(itertools.product([task], interface_items)):
                            count = count + 1
                            if count > 20000:
                                break
                else:
                    for _ in itertools.product(task_items, interface_items):
                        count = count + 1
                        if count > 20000:
                            break
            if count >= 20000:
                count = '&gt; 20000'
            return {'count': count}
        else:
            return {'count': 0}
    except api.Invalid:
        return {'count': 'Could not determine the required number of participants'}

@view_config(route_name='survey.qsheet.data')
@render({'text/html': 'backend/data/qsheet.html'})
def qsheet(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            return {'qsheet': qsheet,
                    'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
    
@view_config(route_name='survey.qsheet.data.attach')
@render({'text/html': 'backend/data/qsheet_attach.html'})
def attach(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    params = AttachDataSetSchema().to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        data_set = dbsession.query(DataSet).filter(DataSet.id==params['dsid']).first()
                        if data_set:
                            dbsession.add(qsheet)
                            qsheet.dataset_id = params['dsid']
                        if data_set.type == 'dataset':
                            request.session.flash('Data set attached', 'info')
                        elif data_set.type == 'permutation':
                            request.session.flash('Permutation attached', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.data', sid=request.matchdict['sid'], qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'e': e}
            else:
                return {'survey' : survey,
                        'qsheet' : qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.data.detach')
@render({'text/html': 'backend/data/qsheet_detach.html'})
def detach(request):
    dbsession = DBSession()
    user = current_user(request)
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(QSheet.id==request.matchdict['qsid']).first()
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                with transaction.manager:
                    qsheet.dataset_id = None
                    dbsession.add(qsheet)
                request.session.flash('Data detached', 'info')
                raise HTTPFound(request.route_url('survey.qsheet.data', sid=request.matchdict['sid'], qsid=request.matchdict['qsid']))
            else:
                if not qsheet.data_set:
                    raise HTTPFound(request.route_url('survey.qsheet.data', sid=survey.id, qsid=qsheet.id))
                return {'survey' : survey,
                        'qsheet' : qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
    