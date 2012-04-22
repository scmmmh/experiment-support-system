# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pywebtools.auth import is_authorised

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.helpers.results import fix_na, get_d_attr_value
from pyquest.models import (DBSession, Survey)
from pyquest.renderer import render
from pyquest.helpers.qsheet import get_attr_groups, get_qg_attr_value,\
    get_qs_attr_value, get_q_attr_value

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
                                    row['data_id'] = answer.data_item_id
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
    def safe_int(value):
        try:
            return int(value)
        except ValueError:
            return 0
    def get_data_identifier(data_item, data_identifier):
        if data_identifier:
            return get_d_attr_value(data_item, data_identifier)
        else:
            return data_item.id
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            data_attr = []
            if survey.data_items:
                data_attr = [('pyquest_id_', 'Internal Identifier')] + [(a.key, a.key) for a in survey.data_items[0].attributes]
            data_identifier = None
            if 'data_identifier' in request.params and request.params['data_identifier'] != 'pyquest_id_':
                if request.params['data_identifier'] in [d[0] for d in data_attr]:
                    data_identifier = request.params['data_identifier']
            columns = ['participant_id']
            for qsheet in survey.qsheets:
                has_data_items = safe_int(get_qs_attr_value(qsheet, 'data-items')) > 0
                for question in qsheet.questions:
                    if question.type != 'text':
                        if question.type in ['multi_choice', 'ranking']:
                            for sub_answer in get_attr_groups(question, 'answer'):
                                if has_data_items:
                                    for data_item in survey.data_items:
                                        columns.append('%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_answer, 'value'), get_data_identifier(data_item, data_identifier)))
                                else:
                                    columns.append('%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_answer, 'value')))
                            if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
                                if has_data_items:
                                    for data_item in survey.data_items:
                                        columns.append('%s.%s._other.%s' % (qsheet.name, question.name, get_data_identifier(data_item, data_identifier)))
                                else:
                                    columns.append('%s.%s._other' % (qsheet.name, question.name))
                        elif question.type in ['single_choice_grid', 'multichoice_group']:
                            for sub_quest in get_attr_groups(question, 'subquestion'):
                                if question.type == 'multichoice_group':
                                    for sub_answer in get_attr_groups(question, 'answer'):
                                        if has_data_items:
                                            for data_item in survey.data_items:
                                                columns.append('%s.%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name'), get_qg_attr_value(sub_answer, 'value'), get_data_identifier(data_item, data_identifier)))
                                        else:
                                            columns.append('%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name'), get_qg_attr_value(sub_answer, 'value')))
                                else:
                                    if has_data_items:
                                        for data_item in survey.data_items:
                                            columns.append('%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name'), get_data_identifier(data_item, data_identifier)))
                                    else:
                                        columns.append('%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name')))
                        else:
                            if has_data_items:
                                for data_item in survey.data_items:
                                    columns.append('%s.%s.%s' % (qsheet.name, question.name, get_data_identifier(data_item, data_identifier)))
                            else:
                                columns.append('%s.%s' % (qsheet.name, question.name))
            rows = []
            for participant in survey.participants:
                row = {'participant_id': participant.id}
                for answer in participant.answers:
                    question = answer.question
                    qsheet = question.qsheet
                    has_data_items = safe_int(get_qs_attr_value(qsheet, 'data-items')) > 0
                    for answer_value in answer.values:
                        if question.type == 'ranking':
                            if has_data_items:
                                row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, get_data_identifier(answer.data_item, data_identifier))] = fix_na(answer_value.value)
                            else:
                                row['%s.%s.%s' % (qsheet.name, question.name, answer_value.name)] = fix_na(answer_value.value)
                        elif question.type == 'single_choice_grid':
                            if has_data_items:
                                row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, get_data_identifier(answer.data_item, data_identifier))] = fix_na(answer_value.value)
                            else:
                                row['%s.%s.%s' % (qsheet.name, question.name, answer_value.name)] = fix_na(answer_value.value)
                        elif question.type == 'multi_choice':
                            if answer_value.value:
                                if has_data_items:
                                    row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.value, get_data_identifier(answer.data_item, data_identifier))] = 1
                                else:
                                    row['%s.%s.%s' % (qsheet.name, question.name, answer_value.value)] = 1
                                if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
                                    if has_data_items:
                                        row['%s.%s._other.%s' % (qsheet.name, question.name, get_data_identifier(answer.data_item, data_identifier))] = 1
                                    else:
                                        row['%s.%s._other' % (qsheet.name, question.name)] = answer_value.value
                        elif question.type == 'multichoice_group':
                            if answer_value.value:
                                if has_data_items:
                                    row['%s.%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, answer_value.value, get_data_identifier(answer.data_item, data_identifier))] = 1
                                else:
                                    row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, answer_value.value)] = 1
                        else:
                            if has_data_items:
                                row['%s.%s.%s' % (qsheet.name, question.name, get_data_identifier(answer.data_item, data_identifier))] = fix_na(answer_value.value)
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
