# -*- coding: utf-8 -*-
'''
Created on 16 Mar 2012

@author: mhall
'''

from sqlalchemy import and_, null
from pyquest.models import (QSheet, DataItem, DataSet)

def question_select(qsheet):
    return [(question.id, question.name) for question in qsheet.questions if question.q_type.answer_schema()]

def sample_for_qsheet(qsheet):
    data_item = {'did': 0}
    if qsheet.dataset:
        data_item['did'] = qsheet.dataset.items[0].id
        for attr in qsheet.dataset.items[0].attributes:
            data_item[attr.key] = attr.value

    return data_item

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

def create_data_item_sets(dbsession, user):
    """Creates DataSets for data items which are attached to qsheets in the old way. Note that for this backwards compatibility
       to work the member DataItem.qsheet_id and the relationshipt QSheet.data_items must continue to exist.
    """
    qsheets = dbsession.query(QSheet).all()
    for qsheet in qsheets:
        ditems = dbsession.query(DataItem).filter(and_(DataItem.qsheet_id==qsheet.id, DataItem.dataset_id==null())).all()
        if (len(ditems) > 0):
            ds = DataSet(name=("QSheet " + str(qsheet.id) + " Dataset"))
            dbsession.add(ds)
            ds.owned_by = user.id
            ds.qsheets.append(qsheet)
            dbsession.flush()
            for ditem in ditems:
                ditem.dataset_id = ds.id
                ditem.qsheet_id = null()
            dbsession.flush()

