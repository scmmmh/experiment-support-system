# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
try:
    import cPickle as pickle
except:
    import pickle
import transaction

from formencode import api
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPNotAcceptable
from pyramid.view import view_config
from random import sample, shuffle
from sqlalchemy import and_

from pyquest.models import (DBSession, Survey, QSheet, DataItem, Participant)
from pyquest.renderer import render
from pyquest.validation import PageSchema, ValidationState, flatten_invalid

def get_instr(qsid, schema):
    for instr in schema:
        if instr['qsid'] == qsid:
            return instr
    return None

def data_item_to_dict(data_item):
    result = {'did': data_item.id}
    for attr in data_item.attributes:
        result[attr.key] = attr.value
    return result

def select_data_items(sid, state, instr, dbsession):
    if 'data_items' in instr:
        data_items = map(lambda d: {'did': d.id},
                         dbsession.query(DataItem).filter(DataItem.survey_id==sid).all())
        participant = dbsession.query(Participant).filter(Participant.id==state['ptid']).first()
        pt_answers = pickle.loads(str(participant.answers))
        filter_list = []
        if state['qsid'] in pt_answers:
            filter_list = map(lambda d: unicode(d), pt_answers[state['qsid']]['items'].keys())
        data_items = filter(lambda d: str(d['did']) not in filter_list, data_items)
        if len(data_items) > instr['data_items']['count']:
            return sample(data_items, instr['data_items']['count'])
        else:
            shuffle(data_items)
            return data_items
    else:
        return[{'did': 'none'}]

def load_data_items(state, dbsession):
    data_items = dbsession.query(DataItem).filter(DataItem.id.in_(map(lambda d: d['did'], state['dids']))).all()
    if data_items:
        return map(data_item_to_dict, data_items)
    else:
        return [{'did': 'none'}]

def init_state(request, dbsession, survey, survey_schema):
    if 'survey.%s' % request.matchdict['sid'] in request.cookies:
        state = pickle.loads(str(request.cookies['survey.%s' % request.matchdict['sid']]))
    else:
        state = {'qsid': survey_schema[0]['qsid']}
        with transaction.manager:
            participant = Participant(survey_id=survey.id,
                                      answers=pickle.dumps({}))
            dbsession.add(participant)
            dbsession.flush()
            state['ptid'] = participant.id
    return state

def determine_submit_options(instr, state, survey_schema):
    next_instr = get_instr(instr['next_qsid'], survey_schema)
    if next_instr:
        if next_instr['type'] == 'finish':
            if instr['type'] == 'single':
                return ['finish']
            elif instr['type'] == 'repeat':
                return ['more', 'finish']
            else:
                return []
        else:
            if instr['type'] == 'single':
                return ['next']
            elif instr['type'] == 'repeat':
                return ['more', 'next']
            else:
                return ['next']
    else:
        if instr['type'] == 'single':
            return ['finish']
        elif instr['type'] == 'repeat':
            return ['more', 'finish']
        else:
            return []

@view_config(route_name='survey.run')
@render({'text/html': 'frontend/qsheet.html'})
def run_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        if survey.status not in ['running', 'testing']:
            raise HTTPFound(request.route_url('survey.run.inactive', sid=request.matchdict['sid']))
        survey_schema = pickle.loads(str(survey.schema))
        state = init_state(request, dbsession, survey, survey_schema)
        if not state['qsid']:
            raise HTTPFound(request.route_url('survey.run.finished', sid=request.matchdict['sid']))
        instr = get_instr(state['qsid'], survey_schema)
        qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==instr['qsid'],
                                                     QSheet.survey_id==request.matchdict['sid'])).first()
        if not qsheet:
            raise HTTPNotFound()
        if request.method == 'GET':
            if 'dids' not in state:
                state['dids'] = select_data_items(request.matchdict['sid'], state, instr, dbsession)
                if len(state['dids']) == 0:
                    response = HTTPFound(request.route_url('survey.run', sid=request.matchdict['sid']))
                    state['qsid'] = instr['next_qsid']
                    del state['dids']
                    response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
                    raise response
            data_items = load_data_items(state, dbsession)
            request.response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
            return {'survey': survey,
                    'qsheet': qsheet,
                    'data_items': data_items,
                    'submit_options': determine_submit_options(instr, state, survey_schema)}
        elif request.method == 'POST':
            data_items = load_data_items(state, dbsession)
            validator = PageSchema(pickle.loads(str(qsheet.schema)), data_items)
            try:
                qsheet_answers = validator.to_python(request.POST, ValidationState(request=request))
                with transaction.manager:
                    participant = dbsession.query(Participant).filter(Participant.id==state['ptid']).first()
                    pt_answers = pickle.loads(str(participant.answers))
                    if state['qsid'] in pt_answers:
                        pt_answers[state['qsid']]['items'].update(qsheet_answers['items'])
                    else:
                        pt_answers[state['qsid']] = qsheet_answers
                    participant.answers = pickle.dumps(pt_answers)
                if qsheet_answers['_action'] in ['Next', 'Finish']:
                    state['qsid'] = instr['next_qsid']
                del state['dids']
                response = HTTPFound(request.route_url('survey.run', sid=survey.id))
                response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
                raise response
            except api.Invalid as ie:
                ie = flatten_invalid(ie)
                ie.params = request.POST
                return {'survey': survey,
                        'qsheet': qsheet,
                        'data_items': data_items,
                        'submit_options': determine_submit_options(instr, state, survey_schema),
                        'e': ie}
        else:
            raise HTTPNotAcceptable()
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.run.finished')
@render({'text/html': 'frontend/finished.html'})
def finished_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        if survey.status == 'testing':
            request.response.delete_cookie('survey.%s' % request.matchdict['sid'])
        return {'survey': survey}
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.run.inactive')
@render({'text/html': 'frontend/inactive.html'})
def inactive(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        if survey.status in ['running', 'testing']:
            raise HTTPFound(request.route_url('survey.run', sid=request.matchdict['sid']))
        return {'survey': survey}
    else:
        raise HTTPNotFound()
