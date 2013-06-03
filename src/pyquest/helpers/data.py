# -*- coding: utf-8 -*-
'''
Created on 16 Mar 2012

@author: mhall
'''

def question_select(qsheet):
    return [(question.id, question.name) for question in qsheet.questions if question.q_type.answer_schema()]

def sample_for_qsheet(qsheet):
    data_item = {'did': 0}
    if qsheet.data_items:
        data_item['did'] = qsheet.data_items[0].id
        for attr in qsheet.data_items[0].attributes:
            data_item[attr.key] = attr.value
    return [data_item]

def generate_summary(qsheet):
    data_questions = 0
    for question in qsheet.questions:
        if question.q_type.answer_schema():
            data_questions = data_questions + 1
    data_questions = float(data_questions)
    counts = []
    for data_item in qsheet.data_items:
        if data_questions > 0:
            counts.append(len(data_item.answers) / data_questions)
        else:
            counts.append(len(data_item.answers))
    return (len(qsheet.data_items), int(min(counts)), sum(counts) / float(len(counts)), int(max(counts)))
