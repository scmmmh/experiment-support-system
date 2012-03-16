# -*- coding: utf-8 -*-
'''
Created on 16 Mar 2012

@author: mhall
'''

def question_select(survey):
    return [(question.id, '%s.%s' % (qsheet.name, question.name)) for qsheet in survey.qsheets for question in qsheet.questions if question.type != 'text']