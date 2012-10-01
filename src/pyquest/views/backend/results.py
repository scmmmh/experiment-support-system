# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''
from formencode import Schema, validators, foreach, api, variabledecode
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pywebtools.auth import is_authorised
from sqlalchemy import and_

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.helpers.results import fix_na, get_d_attr_value
from pyquest.models import (DBSession, Survey, Answer)
from pyquest.renderer import render
from pyquest.helpers.qsheet import get_attr_groups, get_qg_attr_value,\
    get_qs_attr_value, get_q_attr_value

class DataIdentifierSchema(Schema):
    qsheet = validators.UnicodeString(not_empty=True)
    column = validators.UnicodeString(not_empty=True)
class ByParticipantSchema(Schema):
    columns = foreach.ForEach(validators.UnicodeString(not_empty=True))
    data_identifier = foreach.ForEach(DataIdentifierSchema(), if_empty=[])
    na_value = validators.UnicodeString()

    pre_validators = [variabledecode.NestedVariables()]

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
            columns = ['page_', 'participant_id_']
            data_item_columns = []
            for qsheet in survey.qsheets:
                if qsheet.data_items:
                    for attr in qsheet.data_items[0].attributes:
                        data_item_columns.append('%s.%s' % (qsheet.name, attr.key))
            if data_item_columns:
                columns.append('data_id_')
                columns.extend(data_item_columns)
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
                                        row['%s.%s' % (qsheet.name, attr.key)] = attr.value
                                rows.append(row)
            return {'columns': columns,
                    'rows': rows,
                    'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def get_data_identifier(data_item, data_identifier):
    if data_identifier:
        return get_d_attr_value(data_item, data_identifier, default=data_item.id)
    else:
        return data_item.id

def generate_columns(survey, selected_columns, data_identifiers):
    columns = []
    for qsheet in survey.qsheets:
        for question in qsheet.questions:
            if '%s.%s' % (qsheet.name, question.name) in selected_columns:
                if question.type in ['multi_choice', 'ranking']:
                    for sub_answer in get_attr_groups(question, 'answer'):
                        if qsheet.data_items:
                            for data_item in qsheet.data_items:
                                columns.append('%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_answer, 'value'), get_data_identifier(data_item, data_identifiers[qsheet.name])))
                        else:
                            columns.append('%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_answer, 'value')))
                    if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
                        if qsheet.data_items:
                            for data_item in qsheet.data_items:
                                columns.append('%s.%s._other.%s' % (qsheet.name, question.name, get_data_identifier(data_item, data_identifiers[qsheet.name])))
                        else:
                            columns.append('%s.%s._other' % (qsheet.name, question.name))
                elif question.type in ['single_choice_grid', 'multi_choice_grid']:
                    for sub_quest in get_attr_groups(question, 'subquestion'):
                        if question.type == 'multi_choice_grid':
                            for sub_answer in get_attr_groups(question, 'answer'):
                                if qsheet.data_items:
                                    for data_item in qsheet.data_items:
                                        columns.append('%s.%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name'), get_qg_attr_value(sub_answer, 'value'), get_data_identifier(data_item, data_identifiers[qsheet.name])))
                                else:
                                    columns.append('%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name'), get_qg_attr_value(sub_answer, 'value')))
                        else:
                            if qsheet.data_items:
                                for data_item in qsheet.data_items:
                                    columns.append('%s.%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name'), get_data_identifier(data_item, data_identifiers[qsheet.name])))
                            else:
                                columns.append('%s.%s.%s' % (qsheet.name, question.name, get_qg_attr_value(sub_quest, 'name')))
                else:
                    if qsheet.data_items:
                        for data_item in qsheet.data_items:
                            columns.append('%s.%s.%s' % (qsheet.name, question.name, get_data_identifier(data_item, data_identifiers[qsheet.name])))
                    else:
                        columns.append('%s.%s' % (qsheet.name, question.name))
    columns.sort()
    if '_.completed' in selected_columns:
        columns.insert(0, 'completed_')
    if '_.participant_id' in selected_columns:
        columns.insert(0, 'participant_id_')
    return columns

@view_config(route_name='survey.results.by_participant')
@view_config(route_name='survey.results.by_participant.ext')
@render({'text/html': 'backend/results/by_participant.html', 'text/csv': ''}, expose_response_format=True)
def participant(request, response_format='text/html'):
    def safe_int(value):
        try:
            return int(value)
        except ValueError:
            return 0
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            selected_columns = ['_.participant_id', '_.completed']
            data_identifiers = {}
            for qsheet in survey.qsheets:
                for question in qsheet.questions:
                    if question.type not in ['text', 'auto_commit']:
                        selected_columns.append('%s.%s' % (qsheet.name, question.name))
                if qsheet.data_items:
                    data_identifiers[qsheet.name] = 'id_'
            selected_columns.sort()
            columns = generate_columns(survey, selected_columns, data_identifiers)
            na_value = 'NA'
            if request.method == 'POST':
                try :
                    params = ByParticipantSchema().to_python(request.POST)
                    selected_columns = params['columns']
                    selected_columns.sort()
                    for data_identifier in params['data_identifier']:
                        data_identifiers[data_identifier['qsheet']] = data_identifier['column']
                    columns = generate_columns(survey, selected_columns, data_identifiers)
                    na_value = params['na_value']
                except api.Invalid as e:
                    e.params = request.POST
                    return {'e': e,
                            'survey': survey,
                            'selected_columns': selected_columns,
                            'data_identifiers': data_identifiers,
                            'na_value': na_value,
                            'columns': columns,
                            'rows': []}
            rows = []
            count = 0
            for participant in survey.participants:
                row = {'participant_id_': participant.id}
                completed = True
                for qsheet in survey.qsheets:
                    for question in qsheet.questions:
                        if question.required:
                            if not dbsession.query(Answer).filter(and_(Answer.participant_id==participant.id,
                                                                       Answer.question_id==question.id)).first():
                                completed = False
                                break
                    if not completed:
                        break
                row['completed_'] = completed
                for answer in participant.answers:
                    question = answer.question
                    qsheet = question.qsheet
                    has_data_items = safe_int(get_qs_attr_value(qsheet, 'data-items')) > 0
                    for answer_value in answer.values:
                        if question.type == 'ranking':
                            if has_data_items:
                                row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, get_data_identifier(answer.data_item, data_identifiers[qsheet.name]))] = fix_na(answer_value.value, na_value)
                            else:
                                row['%s.%s.%s' % (qsheet.name, question.name, answer_value.name)] = fix_na(answer_value.value, na_value)
                        elif question.type == 'single_choice_grid':
                            if has_data_items:
                                row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, get_data_identifier(answer.data_item, data_identifiers[qsheet.name]))] = fix_na(answer_value.value, na_value)
                            else:
                                row['%s.%s.%s' % (qsheet.name, question.name, answer_value.name)] = fix_na(answer_value.value, na_value)
                        elif question.type == 'multi_choice':
                            if answer_value.value:
                                if has_data_items:
                                    row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.value, get_data_identifier(answer.data_item, data_identifiers[qsheet.name]))] = 1
                                else:
                                    row['%s.%s.%s' % (qsheet.name, question.name, answer_value.value)] = 1
                                if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
                                    if has_data_items:
                                        row['%s.%s._other.%s' % (qsheet.name, question.name, get_data_identifier(answer.data_item, data_identifiers[qsheet.name]))] = 1
                                    else:
                                        row['%s.%s._other' % (qsheet.name, question.name)] = answer_value.value
                        elif question.type == 'multi_choice_grid':
                            if answer_value.value:
                                if has_data_items:
                                    row['%s.%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, answer_value.value, get_data_identifier(answer.data_item, data_identifiers[qsheet.name]))] = 1
                                else:
                                    row['%s.%s.%s.%s' % (qsheet.name, question.name, answer_value.name, answer_value.value)] = 1
                        else:
                            if has_data_items:
                                row['%s.%s.%s' % (qsheet.name, question.name, get_data_identifier(answer.data_item, data_identifiers[qsheet.name]))] = fix_na(answer_value.value, na_value)
                            else:
                                row['%s.%s' % (qsheet.name, question.name)] = fix_na(answer_value.value, na_value)
                for key in columns:
                    if key not in row:
                        row[key] = na_value
                rows.append(row)
                count = count + 1
                if response_format == 'text/html' and count >= 20:
                    break
            return {'selected_columns': selected_columns,
                    'data_identifiers': data_identifiers,
                    'na_value': na_value,
                    'columns': columns,
                    'rows': rows,
                    'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
