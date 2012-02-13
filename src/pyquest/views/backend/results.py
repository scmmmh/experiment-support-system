# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''
try:
    import cPickle as pickle
except:
    import pickle
import transaction

from formencode import Schema, validators, api, foreach
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, DataItem)
from pyquest.renderer import render

@view_config(route_name='survey.results')
@render({'text/html': 'backend/results/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            qsheets = []
            for qsheet in survey.qsheets:
                qsheets.append({'qsid': unicode(qsheet.id),
                                'schema': pickle.loads(str(qsheet.schema))})
            participants = []
            for participant in survey.participants:
                participants.append(pickle.loads(str(participant.answers)))
            return {'survey': survey,
                    'qsheets': qsheets,
                    'participants': participants}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def flatten_answers(question, answer):
    if isinstance(answer, list):
        return map(lambda a: (question, a), answer)
    elif isinstance(answer, dict):
        tmp = []
        for (key, value) in answer.items():
            for (question2, answer2) in flatten_answers(key, value):
                tmp.append(('%s.%s' % (question, question2), answer2))
        return tmp
    else:
        return [(question, answer)]

@view_config(route_name='survey.results.data')
@view_config(route_name='survey.results.data.ext')
@render({'text/html': 'backend/results/data.html', 'text/csv': ''})
def raw_data(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            rows = []
            columns = ['page', 'data_id', 'participant_id']
            if len(survey.data_items) > 0:
                for attr in survey.data_items[0].attributes:
                    columns.append(attr.key) 
            columns.append('question')
            columns.append('answer')
            qsid_mapping = {}
            for qsheet in survey.qsheets:
                qsid_mapping[unicode(qsheet.id)] = qsheet.name
            for participant in survey.participants:
                answers = pickle.loads(str(participant.answers))
                for (qsid, value) in answers.items():
                    if 'items' in value:
                        for (did, questions) in value['items'].items():
                            for (question, answer) in questions.items():
                                if not question.endswith('_'):
                                    flat_items = flatten_answers(question, answer)
                                    for(question, answer) in flat_items:
                                        row = {'page': qsid_mapping[qsid],
                                               'data_id': did,
                                               'participant_id': participant.id,
                                               'question': question,
                                               'answer': answer}
                                        if did != 'none':
                                            data_item = dbsession.query(DataItem).filter(DataItem.id==did).first()
                                            if data_item:
                                                for attr in data_item.attributes:
                                                    row[attr.key] = attr.value
                                        rows.append(row)
            return {'columns': columns,
                    'rows': rows,
                    'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.results.participant')
@view_config(route_name='survey.results.participant.ext')
@render({'text/html': 'backend/results/participant.html', 'text/csv': ''})
def participant(request):
    def safe_int(item):
        try:
            return int(item)
        except ValueError:
            return item
    def cmp_columns(col_a, col_b):
        parts_a = map(safe_int, col_a.split('.'))
        parts_b = map(safe_int, col_b.split('.'))
        if parts_a[0] == parts_b[0]:
            if len(parts_a) > 1 and len(parts_b) > 1:
                if parts_a[1] == parts_b[1]:
                    if len(parts_a) > 2 and len(parts_b) > 2:
                        if parts_a[2] < parts_b[2]:
                            return -1
                        elif parts_a[2] > parts_b[2]:
                            return 1
                elif parts_a[1] < parts_b[1]:
                    return -1
                elif parts_a[1] > parts_b[1]:
                    return 1
        elif parts_a[0] < parts_b[0]:
            return -1
        elif parts_a[0] > parts_b[0]:
            return 1
        return 0
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            if len(survey.all_items) > 0:
                data_attr = map(lambda d: (d.key, d.key), survey.all_items[0].attributes)
                data_attr.insert(0, ('did_', 'System Identifier'))
            else:
                data_attr = []
            data_identifier = None
            if 'data_identifier' in request.params and request.params['data_identifier'] != 'did_' and \
                    request.params['data_identifier'] in map(lambda d: d[0], data_attr):
                data_identifier = request.params['data_identifier']
            rows = []
            columns = []
            did_mapping = {}
            for data_item in survey.all_items:
                if data_identifier:
                    for attr in data_item.attributes:
                        if attr['key'] == data_identifier:
                            did_mapping[unicode(data_item.id)] = attr['value']
                            break
                else:
                    did_mapping[unicode(data_item.id)] = unicode(data_item.id)
            qsid_mapping = {}
            schema = pickle.loads(str(survey.schema))
            for sheet in schema:
                qsheet = dbsession.query(QSheet).filter(QSheet.id==sheet['qsid']).first()
                qsid_mapping[unicode(qsheet.id)] = qsheet.name
                qs_schema = pickle.loads(str(qsheet.schema))
                for (question, attr) in qs_schema.items():
                    if attr['type'] in ['multi_in_list', 'all_in_list']:
                        for value in attr['values']:
                            if 'data_items' in sheet:
                                for data_item in survey.all_items:
                                    columns.append('%s.%s.%s.%s' % (qsid_mapping[unicode(qsheet.id)], question, value, did_mapping[unicode(data_item.id)]))
                            else:
                                columns.append('%s.%s.%s' % (qsid_mapping[unicode(qsheet.id)], question, value))
                    elif attr['type'] == 'compound':
                        for (sub_question, sub_attr) in attr['fields'].items():
                            if sub_attr['type'] == 'multi_in_list':
                                for sub_value in sub_attr['values']:
                                    if 'data_items' in sheet:
                                        for data_item in survey.all_items:
                                            columns.append('%s.%s.%s.%s.%s' % (qsid_mapping[unicode(qsheet.id)], question, sub_question, sub_value, did_mapping[unicode(data_item.id)]))
                                    else:
                                        columns.append('%s.%s.%s.%s' % (qsid_mapping[unicode(qsheet.id)], question, sub_question, sub_value))
                            else:
                                if 'data_items' in sheet:
                                    for data_item in survey.all_items:
                                        columns.append('%s.%s.%s.%s' % (qsid_mapping[unicode(qsheet.id)], question, sub_question, did_mapping[unicode(data_item.id)]))
                                else:
                                    columns.append('%s.%s.%s' % (qsid_mapping[unicode(qsheet.id)], question, sub_question))
                    else:
                        if 'data_items' in sheet:
                            for data_item in survey.all_items:
                                columns.append('%s.%s.%s' % (qsid_mapping[unicode(qsheet.id)], question, did_mapping[unicode(data_item.id)]))
                        else:
                            columns.append('%s.%s' % (qsid_mapping[unicode(qsheet.id)], question))
            columns.sort(cmp=cmp_columns)
            columns.insert(0, 'participant_id')
            for participant in survey.participants:
                answers = pickle.loads(str(participant.answers))
                row = {'participant_id': participant.id}
                for (qsid, value) in answers.items():
                    if 'items' in value:
                        for (did, questions) in value['items'].items():
                            for (question, answer) in questions.items():
                                if not question.endswith('_'):
                                    for (flat_question, flat_answer) in flatten_answers(question, answer):
                                        if did == 'none':
                                            question_id = '%s.%s' % (qsid_mapping[qsid], flat_question)
                                            if question_id in columns:
                                                row[question_id] = flat_answer
                                            else:
                                                question_id = '%s.%s.%s' % (qsid_mapping[qsid], flat_question, flat_answer)
                                                if question_id in columns:
                                                    row[question_id] = 1
                                        else:
                                            question_id = '%s.%s.%s' % (qsid_mapping[qsid], flat_question, did_mapping[did])
                                            if question_id in columns:
                                                row[question_id] = flat_answer
                                            else:
                                                question_id = '%s.%s.%s.%s' % (qsid_mapping[qsid], flat_question, flat_answer, did_mapping[did])
                                                if question_id in columns:
                                                    row[question_id] = 1
                rows.append(row)
            return {'columns': columns,
                    'rows': rows,
                    'survey': survey,
                    'data_attr': data_attr,
                    'data_identifier': data_identifier}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
