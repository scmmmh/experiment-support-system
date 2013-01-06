# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''

from random import sample

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
