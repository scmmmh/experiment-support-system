# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''

from random import sample
import re

def fix_na(value, na_value='N/A'):
    if value:
        return value.encode('utf-8')
    else:
        return na_value

def answer_count(question, sub_quest=None):
    if sub_quest:
        count = 0
        for answer in question.answers:
            for value in answer.values:
                if value.name == sub_quest:
                    count = count + 1
                    break
        return count
    else:
        return len(question.answers)

def sample_answer(question, sub_quest=None):
    if len(question.answers) > 0:
        if sub_quest:
            return ', '.join([fix_na(av.value) for av in list(sample(question.answers, 1)[0].values) if av.name == sub_quest])
        else:
            return ', '.join([fix_na(av.value) for av in list(sample(question.answers, 1)[0].values)])
    else:
        return None

def completed_count(survey):
    participants = [len(set([a.participant_id for a in question.answers])) for qsheet in survey.qsheets for question in qsheet.questions if question.q_type.answer_schema() and question.required]
    if participants:
        return min(participants)
    else:
        return 0

def has_data_questions(qsheet):
    for question in qsheet.questions:
        if question.q_type.answer_schema():
            return True
    return False

def spss_safe_string(name):
    """ 
    Makes string name safe for use as an spss variable name by arbitrary substitutions.
    These remove any characters which are not allowed and also remove '_' and '.' when 
    they are at the end of the name.
    :param name: The name to be processed
    :return: An SPSS safe version of name
    """
    name = re.sub('[^a-zA-Z0-9.]', '', name)
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
