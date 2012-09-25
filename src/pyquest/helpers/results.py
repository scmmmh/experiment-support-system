# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''

from random import sample

def fix_na(value):
    if value:
        return value
    else:
        return 'N/A'
    
def sample_question_answer(question, subquest=None):
    if len(question.answers) > 0:
        if subquest:
            return ', '.join([fix_na(av.value) for av in list(sample(question.answers, 1)[0].values) if av.name==subquest])
        else:
            return ', '.join([fix_na(av.value) for av in list(sample(question.answers, 1)[0].values)])
    else:
        return None

def sample_data_answer(data_item):
    if len(data_item.answers) > 0:
        return ', '.join([fix_na(av.value) for av in list(sample(data_item.answers, 1)[0].values)])
    else:
        return None

def completed_count(survey):
    participants = [len(set([a.participant_id for a in question.answers])) for qsheet in survey.qsheets for question in qsheet.questions if question.type != 'text' and question.required]
    if participants:
        return min(participants)
    else:
        return 0

def get_d_attr(qsheet, key):
    for attr in qsheet.attributes:
        if attr.key == key:
            return attr
    return None

def get_d_attr_value(qsheet, key):
    attr = get_d_attr(qsheet, key)
    if attr:
        return attr.value
    else:
        return None

def has_data_questions(qsheet):
    for question in qsheet.questions:
        if question.type != 'text':
            return True
    return False
