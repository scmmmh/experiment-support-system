# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''
from formencode import Schema, validators, api, foreach
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_
from pywebtools.auth import is_authorised

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.helpers.results import fix_na
from pyquest.models import (DBSession, Survey, QSheet, DataItem)
from pyquest.renderer import render
from pyquest.helpers.qsheet import get_attr_groups, get_qg_attr_value

@view_config(route_name='survey.results')
@render({'text/html': 'backend/results/index.html'})
def index(request):
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

@view_config(route_name='survey.results.by_question')
@view_config(route_name='survey.results.by_question.ext')
@render({'text/html': 'backend/results/by_question.html', 'text/csv': ''})
def raw_data(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            rows = []
            columns = ['page', 'participant_id']
            if len(survey.data_items) > 0:
                columns.append('data_id')
                if len(survey.data_items) > 0:
                    for attr in survey.data_items[0].attributes:
                        columns.append(attr.key) 
            columns.append('question')
            columns.append('answer')
            for qsheet in survey.qsheets:
                for question in qsheet.questions:
                    if question.type != 'text':
                        for answer in question.answers:
                            for answer_value in answer.values:
                                row = {}
                                if answer_value.name:
                                    row = {'page': qsheet.name,
                                           'participant_id': answer.participant_id,
                                           'question': '%s.%s' % (question.name, answer_value.name),
                                           'answer': fix_na(answer_value.value)}
                                else:
                                    row = {'page': qsheet.name,
                                           'participant_id': answer.participant_id,
                                           'question': question.name,
                                           'answer': fix_na(answer_value.value)}
                                if answer.data_item_id:
                                    row['data_item_id'] = answer.data_item_id
                                    for attr in answer.data_item.attributes:
                                        row[attr.key] = attr.value
                                rows.append(row)
            return {'columns': columns,
                    'rows': rows,
                    'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.results.by_participant')
@view_config(route_name='survey.results.by_participant.ext')
@render({'text/html': 'backend/results/by_participant.html', 'text/csv': ''})
def participant(request):
    def safe_int(item):
        try:
            return int(item)
        except ValueError:
            return item
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            data_attr = []
            data_identifier = None
            columns = ['participant_id']
            for qsheet in survey.qsheets:
                for question in qsheet.questions:
                    if question.type != 'text':
                        if question.type in ['multichoice', 'ranking']:
                            for sub_answer in get_attr_groups(question, 'answer'):
                                columns.append('%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_answer, 'value')))
                        elif question.type in ['rating_group', 'multichoice_group']:
                            for sub_quest in get_attr_groups(question, 'subquestion'):
                                if question.type == 'multichoice_group':
                                    for sub_answer in get_attr_groups(question, 'answer'):
                                        columns.append('%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name'), get_qg_attr_value(sub_answer, 'value')))
                                else:
                                    columns.append('%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name')))
                        else:
                            columns.append('%s.%s' % (qsheet.name, question.name))
            rows = []
            for participant in survey.participants:
                row = {'participant_id': participant.id}
                for answer in participant.answers:
                    question = answer.question
                    qsheet = question.qsheet
                    for answer_value in answer.values:
                        if question.type == 'ranking':
                            row['%s.%s.%s' % (qsheet.name, question.name, answer_value.name)] = fix_na(answer_value.value)
                        elif question.type == 'rating_group':
                            row['%s.%s.%s' % (qsheet.name, question.name, answer_value.name)] = fix_na(answer_value.value)
                        elif question.type == 'multichoice':
                            if answer_value.value:
                                row['%s.%s.%s' % (qsheet.name, question.name, answer_value.value)] = 1
                        elif question.type == 'multichoice_group':
                            if answer_value.value:
                                row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, answer_value.value)] = 1
                        else:
                            row['%s.%s' % (qsheet.name, question.name)] = fix_na(answer_value.value)
                for key in columns:
                    if key not in row:
                        row[key] = 'N/A'
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
