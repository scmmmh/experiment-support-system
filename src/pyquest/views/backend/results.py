# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''
import json
import re

from formencode import Schema, validators, foreach, api, variabledecode
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pywebtools.auth import is_authorised
from pywebtools.renderer import render
from sqlalchemy import and_

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.helpers.results import fix_na
from pyquest.models import (DBSession, Survey, Answer, AnswerValue)
from pyquest.util import load_question_schema_params


class DataIdentifierSchema(Schema):
    qsheet = validators.UnicodeString(not_empty=True)
    column = validators.UnicodeString(not_empty=True)
    
class ByParticipantSchema(Schema):
    columns = foreach.ForEach(validators.UnicodeString(not_empty=True))
    data_identifier = foreach.ForEach(DataIdentifierSchema(), if_empty=[])
    na_value = validators.UnicodeString()
    spss_safe = validators.Bool()

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
def by_question(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if request.method == 'POST':
            try :
                params = ByParticipantSchema().to_python(request.POST)
                na_value = params['na_value']
                spss_safe = params['spss_safe']
            except api.Invalid as e:
                e.params = request.POST
                return {'e' : e,
                        'columns': [],
                        'rows': [],
                        'na_value': na_value,
                        'spss_safe': spss_safe,
                        'survey': survey}
        else:
            na_value = 'NA'
            spss_safe = False

        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            rows = []
            columns = ['page', 'participant_id']
            data_item_columns = []
            for qsheet in survey.qsheets:
                if qsheet.data_set:
                    for attr in qsheet.data_set.items[0].attributes:
                        column_name = '%s.%s' % (qsheet.data_set.name, attr.key.key)
                        if column_name not in data_item_columns:
                            data_item_columns.append(column_name)
            if data_item_columns:
                columns.append('data_id')
                columns.extend(data_item_columns)
            columns.append('question')
            columns.append('answer')
            for qsheet in survey.qsheets:
                for question in qsheet.questions:
                    if question.q_type.answer_schema():
                        for answer in question.answers:
                            for answer_value in answer.values:
                                row = {}
                                if answer_value.name:
                                    if qsheet.data_set and qsheet.data_set.type == 'permutationset':
                                        sub_answer = answer_value.name.split('.')
                                        if len(sub_answer) > 1:
                                            row = {'page': qsheet.name,
                                                   'participant_id': answer.participant_id,
                                                   'question': '%s.%s' % (question.name, sub_answer[1]),
                                                   'answer': fix_na(answer_value.value, na_value)}
                                        else:
                                            row = {'page': qsheet.name,
                                                   'participant_id': answer.participant_id,
                                                   'question': question.name,
                                                   'answer': fix_na(answer_value.value, na_value)}
                                    else:
                                        row = {'page': qsheet.name,
                                               'participant_id': answer.participant_id,
                                               'question': '%s.%s' % (question.name, answer_value.name),
                                               'answer': fix_na(answer_value.value, na_value)}
                                else:
                                    row = {'page': qsheet.name,
                                           'participant_id': answer.participant_id,
                                           'question': question.name,
                                           'answer': fix_na(answer_value.value, na_value)}
                                if answer.data_item_id:
                                    row['data_id'] = answer.data_item_id
                                    for attr in answer.data_item.attributes:
                                        if qsheet.data_set and qsheet.data_set.type == 'permutationset' and answer_value.name:
                                            print answer_value.name
                                            row['%s.%s' % (qsheet.data_set.name, attr.key.key)] = json.dumps(json.loads(attr.value)[int(answer_value.name.split('.')[0])]).encode('utf-8')
                                        else:
                                            row['%s.%s' % (qsheet.data_set.name, attr.key.key)] = attr.value.encode('utf-8')
                                rows.append(row)
            if spss_safe:
                columns, rows = make_spss_safe(columns, rows)
            return {'columns': columns,
                    'rows': rows,
                    'na_value': na_value,
                    'spss_safe': spss_safe,
                    'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def get_data_identifier(data_item, data_identifier):
    if data_identifier:
        for attr in data_item.attributes:
            if attr.key == data_identifier:
                return attr.value
        return data_item.id
    else:
        return data_item.id

def generate_question_columns(base_name, question, q_schema, data_items, data_identifier, dbsession):
    if 'params' in q_schema:
        v_params = load_question_schema_params(q_schema['params'], question)
    else:
        v_params = {}
    columns = []
    if q_schema['type'] == 'choice':
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            for sub_answer in question.attr_value(q_schema['attr'], multi=True):
                columns.append('%s.%s' % (base_name, sub_answer))
            if question.attr_value('further.allow_other', default='no') == 'single':
                columns.append('%s.other_' % (base_name))
        else:
            columns.append(base_name)
    elif q_schema['type'] == 'multiple':
        for sub_question in question.attr_value(q_schema['attr'], multi=True):
            columns.extend(generate_question_columns('%s.%s' % (base_name, sub_question), question, q_schema['schema'], data_items, data_identifier, dbsession))
    elif q_schema['type'] == 'ranking':
        for sub_answer in question.attr_value(q_schema['attr'], multi=True):
            columns.append('%s.%s' % (base_name, sub_answer))
    else:
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            for (value,) in dbsession.query(AnswerValue.value.distinct()).join(Answer).filter(Answer.question_id==question.id):
                if value:
                    columns.append('%s.%s' % (base_name, value))
        else:
            columns.append(base_name)
    if data_items and q_schema['type'] != 'multiple':
        base_columns = columns
        columns = []
        for data_item in data_items:
            for column in base_columns:
                if data_item.data_set.type == 'permutationset':
                    for idx in range(0, len(json.loads(data_item.attributes[0].value))):
                        columns.append('%s.%s.%s' % (column, get_data_identifier(data_item, data_identifier), idx))
                else:
                    columns.append('%s.%s' % (column, get_data_identifier(data_item, data_identifier)))
    return columns

def generate_columns(survey, selected_columns, data_identifiers, dbsession):
    columns = []
    for qsheet in survey.qsheets:
        for question in qsheet.questions:
            if '%s.%s' % (qsheet.name, question.name) in selected_columns:
                columns.extend(generate_question_columns('%s.%s' % (qsheet.name, question.name),
                                                         question,
                                                         question.q_type.answer_schema(),
                                                         qsheet.data_set.items if qsheet.data_set else None,
                                                         data_identifiers[qsheet.name] if qsheet.name in data_identifiers else '',
                                                         dbsession))
    columns.sort()
    if '_.completed' in selected_columns:
        columns.insert(0, 'completed_')
    if '_.participant_id' in selected_columns:
        columns.insert(0, 'participant_id_')
    return columns

@view_config(route_name='survey.results.by_participant')
@view_config(route_name='survey.results.by_participant.ext')
@render({'text/html': 'backend/results/by_participant.html', 'text/csv': ''})
def by_participant(request):
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
                    if question.q_type.answer_schema():
                        selected_columns.append('%s.%s' % (qsheet.name, question.name))
                if qsheet.data_set:
                    data_identifiers[qsheet.name] = 'id_'
            selected_columns.sort()
            if request.method == 'POST':
                try :
                    params = ByParticipantSchema().to_python(request.POST)
                    selected_columns = params['columns']
                    selected_columns.sort()
                    for data_identifier in params['data_identifier']:
                        data_identifiers[data_identifier['qsheet']] = data_identifier['column']
                    columns = generate_columns(survey, selected_columns, data_identifiers, dbsession)
                    na_value = params['na_value']
                    spss_safe = params['spss_safe']
                except api.Invalid as e:
                    e.params = request.POST
                    return {'e': e,
                            'survey': survey,
                            'selected_columns': selected_columns,
                            'data_identifiers': data_identifiers,
                            'na_value': na_value,
                            'spss_safe': spss_safe,
                            'columns': columns,
                            'rows': []}
            else:
                columns = generate_columns(survey, selected_columns, data_identifiers, dbsession)
                na_value = 'NA'
                spss_safe = False
            rows = []
            count = 0
            for participant in survey.participants:
                row = dict([(c, na_value) for c in columns])
                if 'participant_id_' in columns:
                    row['participant_id_'] = participant.id
                completed = True
                for qsheet in survey.qsheets:
                    for question in qsheet.questions:
                        if question.required:
                            if not dbsession.query(Answer).filter(and_(Answer.participant_id==participant.id,
                                                                       Answer.question_id==question.id)).first():
                                completed = False
                        if '%s.%s' % (qsheet.name, question.name) not in selected_columns:
                            continue
                        q_schema = question.q_type.answer_schema()
                        if not q_schema:
                            continue
                        if 'params' in q_schema:
                            v_params = load_question_schema_params(q_schema['params'], question)
                        elif q_schema['type'] == 'multiple' and 'params' in q_schema['schema']:
                            v_params = load_question_schema_params(q_schema['schema']['params'], question)
                        else:
                            v_params = {}
                        query = dbsession.query(AnswerValue).join(Answer).filter(and_(Answer.participant_id==participant.id,
                                                                                      Answer.question_id==question.id))
                        for answer_value in query:
                            key = '%s.%s' % (qsheet.name, question.name)
                            value = fix_na(answer_value.value, na_value)
                            if q_schema['type'] == 'choice':
                                if 'allow_multiple' in v_params and v_params['allow_multiple']:
                                    if '%s.%s.%s' % (qsheet.name, question.name, answer_value.value) in columns:
                                        key = '%s.%s.%s' % (qsheet.name, question.name, answer_value.value)
                                        value = 1
                                    else:
                                        key = '%s.%s.other_' % (qsheet.name, question.name)
                            elif q_schema['type'] == 'multiple':
                                if answer_value.answer.data_item and answer_value.answer.data_item.data_set and answer_value.answer.data_item.data_set.type == 'permutationset':
                                    answer_name = answer_value.name.split('.')[1]
                                else:
                                    answer_name = answer_value.name
                                if 'allow_multiple' in v_params and v_params['allow_multiple']:
                                    if answer_value.value:
                                        key = '%s.%s.%s.%s' % (qsheet.name, question.name, answer_name, answer_value.value)
                                        value = 1
                                    else:
                                        continue
                                else:
                                    key = '%s.%s.%s' % (qsheet.name, question.name, answer_name)
                            elif q_schema['type'] == 'ranking':
                                if answer_value.answer.data_item and answer_value.answer.data_item.data_set and answer_value.answer.data_item.data_set.type == 'permutationset':
                                    answer_name = answer_value.name.split('.')[1]
                                else:
                                    answer_name = answer_value.name
                                key = '%s.%s.%s' % (qsheet.name, question.name, answer_name)
                            else:
                                if 'allow_multiple' in v_params and v_params['allow_multiple']:
                                    key = '%s.%s.%s' % (qsheet.name, question.name, answer_value.value)
                                    value = 1
                            if answer_value.answer.data_item:
                                if answer_value.answer.data_item.data_set.type == 'permutationset':
                                    key = '%s.%s.%s' % (key, get_data_identifier(answer_value.answer.data_item, data_identifiers[qsheet.name]), answer_value.name.split('.')[0])
                                else:
                                    key = '%s.%s' % (key, get_data_identifier(answer_value.answer.data_item, data_identifiers[qsheet.name]))
                            if isinstance(value, unicode):
                                value = value.encode('utf-8')
                            print key
                            row[key] = value
                if 'completed_' in columns:
                    row['completed_'] = completed
                rows.append(row)
                count = count + 1
            if spss_safe:
                columns, rows = make_spss_safe(columns, rows)
            return {'selected_columns': selected_columns,
                    'data_identifiers': data_identifiers,
                    'na_value': na_value,
                    'spss_safe': spss_safe,
                    'columns': columns,
                    'rows': rows,
                    'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def spss_safe_string(name):
    """ 
    Makes string name safe for use as an spss variable name by arbitrary substitutions.
    These remove any characters which are not allowed and also remove '_' and '.' when 
    they are at the end of the name.
    :param name: The name to be processed
    :return: An SPSS safe version of name
    """
    name = re.sub('[^a-zA-Z0-9._]', '', name)
    name = re.sub('_$', '', name)
    name = re.sub('\.$', '', name)
    return name

def make_spss_safe(columns, rows):
    """ 
    Modifies the names in Lists of columns and rows to be SPSS safe.
    :param columns: a List of the columns to be processed 
    :param rows: a List of the rows to be processed, each row is a Dict 
    :return: SPSS safe versions of columns and rows
    """
    old_columns = columns
    old_rows = rows
    columns = []
    rows = []
    for column in old_columns:
        columns.append(spss_safe_string(column))
    for row in old_rows:
        new_row = {}
        for key in row.keys():
            new_row[spss_safe_string(key)] = row[key]
        rows.append(new_row)

    return (columns, rows)



