# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
try:
    import cPickle as pickle
except:
    import pickle
from random import sample

from formencode import api
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_

from pyquest.models import (DBSession, Survey, QSheet, DataItem)
from pyquest.renderer import render
from pyquest.validation import PageSchema, ValidationState, flatten_invalid

@view_config(route_name='survey.start')
def start_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        schema = pickle.loads(str(survey.schema))
        if len(schema) > 0:
            raise HTTPFound(request.route_url('survey.run', sid=survey.id, qsid=schema[0]['qsid']))
        else:
            raise HTTPNotFound()
    else:
        raise HTTPNotFound()

def current_instr(qsid, schema):
    for instr in schema:
        if instr['qsid'] == qsid:
            return instr
    return None

def next_qsheet_id(qsid, schema):
    for instr in schema:
        if instr['qsid'] == qsid:
            return instr['next_qsid']
    return None

@view_config(route_name='survey.run')
@render({'text/html': 'frontend/qsheet.html'})
def run_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    
    survey_schema = pickle.loads(str(survey.schema))
    instr = current_instr(request.matchdict['qsid'], survey_schema)
    if request.method == 'POST':
        if instr['type'] == 'single':
            data_items = [{'did': 0}]
        elif instr['type'] == 'repeat':
            data_items = [{'did': 1}, {'did': 2}, {'did': 3}, {'did': 4}, {'did': 5}]
        validator = PageSchema(pickle.loads(str(qsheet.schema)), data_items)
        try:
            answers = validator.to_python(request.POST, ValidationState(request=request))
            next_qsid = next_qsheet_id(unicode(qsheet.id), survey_schema)
            if next_qsid:
                raise HTTPFound(request.route_url('survey.run', sid=survey.id, qsid=next_qsid))
            else:
                raise HTTPFound(request.route_url('survey.finish', sid=survey.id))
        except api.Invalid as ie:
            ie = flatten_invalid(ie)
            ie.params = request.POST
            return {'survey': survey,
                    'qsheet': qsheet,
                    'data_items': data_items,
                    'e': ie}
    else:
        if instr['type'] == 'single':
            data_items = [{'did': 0}]
        elif instr['type'] == 'repeat':
            data_items = [{'did': 1}, {'did': 2}, {'did': 3}, {'did': 4}, {'did': 5}]
    return {'survey': survey,
            'qsheet': qsheet,
            'data_items': data_items}