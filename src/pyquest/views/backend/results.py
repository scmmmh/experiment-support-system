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
            for participant in survey.participants:
                answers = pickle.loads(str(participant.answers))
                for (qsid, value) in answers.items():
                    if 'items' in value:
                        for (did, questions) in value['items'].items():
                            for (question, answer) in questions.items():
                                if not question.endswith('_'):
                                    row = {'page': qsid,
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
            for participant in survey.participants:
                answers = pickle.loads(str(participant.answers))
                row = {'participant_id': participant.id}
                for (qsid, value) in answers.items():
                    if 'items' in value:
                        for (did, questions) in value['items'].items():
                            for question in questions.keys():
                                if not question.endswith('_'):
                                    if did == 'none':
                                        column_id = '%s.%s' % (qsid, question)
                                    else:
                                        if data_identifier:
                                            data_item = dbsession.query(DataItem).filter(DataItem.id==did).first()
                                            if data_item:
                                                for attr in data_item.attributes:
                                                    if attr.key == data_identifier:
                                                        did_mapping[did] = attr.value
                                                        column_id = '%s.%s.%s' % (qsid, question, attr.value)
                                                        break
                                            else:
                                                did_mapping[did] = did
                                                column_id = '%s.%s.%s' % (qsid, question, did)
                                        else:
                                            did_mapping[did] = did
                                            column_id = '%s.%s.%s' % (qsid, question, did)
                                    if column_id not in columns:
                                        columns.append(column_id)
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
                                    if did == 'none':
                                        row['%s.%s' % (qsid, question)] = answer
                                    else:
                                        row['%s.%s.%s' % (qsid, question, did_mapping[did])] = answer
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
