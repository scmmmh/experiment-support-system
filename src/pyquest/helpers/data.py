# -*- coding: utf-8 -*-
'''
Created on 16 Mar 2012

@author: mhall
'''

def question_select(qsheet):
    return [(question.id, question.name) for question in qsheet.questions if question.type != 'text']

def sample_for_qsheet(qsheet):
    data_item = {'did': 0}
    if qsheet.data_items:
        data_item['did'] = qsheet.data_items[0].id
        for attr in qsheet.data_items[0].attributes:
            data_item[attr.key] = attr.value
    return data_item

def generate_summary(qsheet):
    counts = []
    for data_item in qsheet.data_items:
        counts.append(len(data_item.answers))
    return (len(qsheet.data_items), min(counts), sum(counts) / float(len(counts)), max(counts))
