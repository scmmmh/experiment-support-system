# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
try:
    import cPickle as pickle
except:
    import pickle

from formencode import api
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPNotAcceptable
from pyramid.view import view_config
from random import sample
from sqlalchemy import and_

from pyquest.models import (DBSession, Survey, QSheet, DataItem)
from pyquest.renderer import render
from pyquest.validation import PageSchema, ValidationState, flatten_invalid

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

def data_item_to_dict(data_item):
    result = {'did': data_item.id}
    for attr in data_item.attributes:
        result[attr.key] = attr.value
    return result

def data_items_for_instr(sid, instr, dbsession):
    if 'data_items' in instr:
        data_items = map(lambda d: {'did': d.id},
                         dbsession.query(DataItem).filter(and_(DataItem.survey_id==sid,
                                                               DataItem.control==False)).all())
        return sample(data_items, 5)
    else:
        return[{'did': 'none'}]

def load_data_items(state, dbsession):
    data_items = dbsession.query(DataItem).filter(DataItem.id.in_(map(lambda d: d['did'], state['dids']))).all()
    if data_items:
        return map(data_item_to_dict, data_items)
    else:
        return [{'did': 'none'}]

@view_config(route_name='survey.run')
@render({'text/html': 'frontend/qsheet.html'})
def run_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        survey_schema = pickle.loads(str(survey.schema))
        if request.method == 'GET':
            if 'survey.%s' % request.matchdict['sid'] in request.cookies:
                state = pickle.loads(str(request.cookies['survey.%s' % request.matchdict['sid']]))
            else:
                state = {'qsid': survey_schema[0]['qsid']}
            instr = current_instr(state['qsid'], survey_schema)
            if 'dids' not in state:
                state['dids'] = data_items_for_instr(request.matchdict['sid'], instr, dbsession)
            data_items = load_data_items(state, dbsession)
            qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==state['qsid'],
                                                         QSheet.survey_id==request.matchdict['sid'])).first()
            if not qsheet:
                raise HTTPNotFound()
            request.response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
            return {'survey': survey,
                    'qsheet': qsheet,
                    'data_items': data_items}
        elif request.method == 'POST':
            if 'survey.%s' % request.matchdict['sid'] not in request.cookies:
                raise HTTPFound(request.route_url('survey.run', qsid=request.matchdict['qsid']))
            state = pickle.loads(str(request.cookies['survey.%s' % request.matchdict['sid']]))
            qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==state['qsid'],
                                                         QSheet.survey_id==request.matchdict['sid'])).first()
            if not qsheet:
                raise HTTPNotFound()
            data_items = load_data_items(state, dbsession)
            validator = PageSchema(pickle.loads(str(qsheet.schema)), data_items)
            try:
                answers = validator.to_python(request.POST, ValidationState(request=request))
                next_qsid = next_qsheet_id(unicode(qsheet.id), survey_schema)
                state = {'qsid': next_qsid}
                if next_qsid:
                    response = HTTPFound(request.route_url('survey.run', sid=survey.id, qsid=next_qsid))
                    response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
                    raise response
            except api.Invalid as ie:
                ie = flatten_invalid(ie)
                ie.params = request.POST
                return {'survey': survey,
                        'qsheet': qsheet,
                        'data_items': data_items,
                        'e': ie}
        else:
            raise HTTPNotAcceptable()
    else:
        raise HTTPNotFound()
