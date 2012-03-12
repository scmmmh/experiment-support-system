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
    
def sample_answer(question, subquest=None):
    if len(question.answers) > 0:
        if subquest:
            return ', '.join([fix_na(av.value) for av in list(sample(question.answers, 1)[0].values) if av.name==subquest])
        else:
            return ', '.join([fix_na(av.value) for av in list(sample(question.answers, 1)[0].values)])
    else:
        return None

def completed_count(survey):
    return min([len(question.answers) for qsheet in survey.qsheets for question in qsheet.questions if question.type != 'text'])
