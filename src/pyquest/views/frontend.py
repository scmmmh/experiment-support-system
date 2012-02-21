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
from operator import itemgetter
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPNotAcceptable
from pyramid.view import view_config
from random import sample, shuffle
from sqlalchemy import and_

from pyquest.models import (DBSession, Survey, QSheet, DataItem, Participant,
    DataItemCount)
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
    def data_item_transform(t):
        if t[1]:
            return (t[0], t[1].count)
        else:
            return (t[0], 0)
    if 'source' in instr:
        source_items = map(data_item_transform, dbsession.query(DataItem, DataItemCount).outerjoin(DataItemCount).filter(and_(DataItem.survey_id==sid,
                                                                                                                              DataItem.control==False)).all())
        if len(source_items) > 0:
            filter_list = []
            participant = dbsession.query(Participant).filter(Participant.id==state['ptid']).first()
            pt_answers = pickle.loads(str(participant.answers))
            if state['qsid'] in pt_answers:
                filter_list = map(lambda d: unicode(d), pt_answers[state['qsid']]['items'].keys())
            source_items.sort(key=itemgetter(1))
            data_items = []
            threshold = source_items[0][1]
            max_threshold = source_items[len(source_items) - 1][1]
            print instr
            while len(data_items) < instr['source']['data_items']:
                if threshold > max_threshold:
                    return []
                threshold_items = filter(lambda t: t[1] == threshold and unicode(t[0].id) not in filter_list, source_items)
                required_count = instr['source']['data_items'] - len(data_items)
                if required_count < len(threshold_items):
                    data_items.extend(map(lambda t: {'did': t[0].id}, sample(threshold_items, required_count)))
                else:
                    data_items.extend(map(lambda t: {'did': t[0].id}, threshold_items))
                threshold = threshold + 1
            control_items = map(lambda d: {'did': d.id},
                                dbsession.query(DataItem).filter(and_(DataItem.survey_id==sid,
                                                                      DataItem.control==True)).all())
            if len(control_items) < instr['source']['control_items']:
                data_items.extend(control_items)
            else:
                data_items.extend(sample(control_items, instr['source']['control_items']))
            shuffle(data_items)
            return data_items
        else:
            return []
    else:
        return[{'did': 'none'}]

def update_data_item_counts(state, dids, dbsession):
    for did in dids:
        if did != 'none':
            with transaction.manager:
                count = dbsession.query(DataItemCount).filter(and_(DataItemCount.data_item_id==did,
                                                                   DataItemCount.qsheet_id==state['qsid'])).first()
                if count:
                    count.count = count.count + 1
                else:
                    dbsession.add(DataItemCount(data_item_id=did, qsheet_id=state['qsid'], count=1))
                
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

def get_participant(dbsession, survey, state):
    participant = dbsession.query(Participant).filter(Participant.id==state['ptid']).first()
    if not participant:
        with transaction.manager:
            participant = Participant(survey_id=survey.id, answers=pickle.dumps({}))
            dbsession.add(participant)
            dbsession.flush()
            state['ptid'] = participant.id
        return get_participant(dbsession, survey, state)
    else:
        return participant

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
            response = HTTPFound(request.route_url('survey.run', sid=request.matchdict['sid']))
            response.delete_cookie('survey.%s' % request.matchdict['sid'])
            raise response
        instr = get_instr(state['qsid'], survey_schema)
        if not instr:
            response = HTTPFound(request.route_url('survey.run.finished', sid=request.matchdict['sid']))
            response.delete_cookie('survey.%s' % request.matchdict['sid'])
            raise response
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
                    participant = get_participant(dbsession, survey, state)
                    pt_answers = pickle.loads(str(participant.answers))
                    if state['qsid'] in pt_answers:
                        pt_answers[state['qsid']]['items'].update(qsheet_answers['items'])
                    else:
                        pt_answers[state['qsid']] = qsheet_answers
                    update_data_item_counts(state, qsheet_answers['items'].keys(), dbsession)
                    participant.answers = pickle.dumps(pt_answers)
                    dbsession.add(participant)
                if qsheet_answers['action_'] in ['Next', 'Finish']:
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
