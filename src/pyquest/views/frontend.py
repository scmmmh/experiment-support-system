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

from pyquest.helpers.qsheet import get_qs_attr_value
from pyquest.models import (DBSession, Survey, QSheet, DataItem, Participant,
    DataItemCount, Answer, AnswerValue, Question)
from pyquest.renderer import render
from pyquest.validation import PageSchema, ValidationState, flatten_invalid

def safe_int(value):
    try:
        return int(value)
    except ValueError:
        return None

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

def select_data_items(sid, state, qsheet, dbsession):
    def data_item_transform(t):
        if t[1]:
            return (t[0], t[1].count)
        else:
            return (t[0], 0)
    if get_qs_attr_value(qsheet, 'repeat') == 'single':
        return [{'did': 'none'}]
    elif get_qs_attr_value(qsheet, 'repeat') == 'repeat':
        source_items = map(data_item_transform,
                           dbsession.query(DataItem, DataItemCount).\
                                outerjoin(DataItemCount).filter(and_(DataItem.survey_id==sid,
                                                                     DataItem.control==False,
                                                                     not_(DataItem.id.in_(dbsession.query(Answer.data_item_id).join(Question, QSheet).filter(and_(Answer.participant_id==state['ptid'],
                                                                                                                                                                  QSheet.id==qsheet.id)))))
                                                                ).all())
        if len(source_items) > 0:
            data_items = []
            threshold = source_items[0][1]
            max_threshold = source_items[len(source_items) - 1][1]
            while len(data_items) < int(get_qs_attr_value(qsheet, 'data-items')):
                if threshold > max_threshold:
                    return []
                threshold_items = filter(lambda t: t[1] == threshold and unicode(t[0].id) not in [], source_items)
                required_count = int(get_qs_attr_value(qsheet, 'data-items')) - len(data_items)
                if required_count < len(threshold_items):
                    data_items.extend(map(lambda t: {'did': t[0].id}, sample(threshold_items, required_count)))
                else:
                    data_items.extend(map(lambda t: {'did': t[0].id}, threshold_items))
                threshold = threshold + 1
            control_items = map(lambda d: {'did': d.id},
                                dbsession.query(DataItem).filter(and_(DataItem.survey_id==sid,
                                                                      DataItem.control==True)).all())
            if len(control_items) < int(get_qs_attr_value(qsheet, 'control-items')):
                data_items.extend(control_items)
            else:
                data_items.extend(sample(control_items, int(get_qs_attr_value(qsheet, 'control-items'))))
            shuffle(data_items)
            return data_items
        else:
            return []
    else:
        return []

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
    data_items = dbsession.query(DataItem).filter(DataItem.id.in_([safe_int(d['did']) for d in state['dids'] if safe_int(d['did'])])).all()
    if data_items:
        return map(data_item_to_dict, data_items)
    else:
        return [{'did': 'none'}]

def init_state(request, dbsession, survey):
    if 'survey.%s' % request.matchdict['sid'] in request.cookies:
        state = pickle.loads(str(request.cookies['survey.%s' % request.matchdict['sid']]))
    else:
        state = {'qsid': survey.start_id}
        with transaction.manager:
            participant = Participant(survey_id=survey.id)
            dbsession.add(participant)
            dbsession.flush()
            state['ptid'] = participant.id
    return state

def determine_submit_options(qsheet):
    if get_qs_attr_value(qsheet, 'repeat') == 'single':
        if len(qsheet.next) > 0:
            return ['next']
        else:
            return ['finish']
    elif get_qs_attr_value(qsheet, 'repeat') == 'repeat':
        if len(qsheet.next) > 0:
            return ['more', 'next']
        else:
            return ['more', 'finish']

def get_participant(dbsession, survey, state):
    participant = dbsession.query(Participant).filter(Participant.id==state['ptid']).first()
    if not participant:
        with transaction.manager:
            participant = Participant(survey_id=survey.id)
            dbsession.add(participant)
            dbsession.flush()
            state['ptid'] = participant.id
        return get_participant(dbsession, survey, state)
    else:
        return participant

def next_qsheet(qsheet):
    for transition in qsheet.next:
        return transition.target
    return None

@view_config(route_name='survey.run')
@render({'text/html': 'frontend/qsheet.html'})
def run_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        if survey.status not in ['running', 'testing']:
            raise HTTPFound(request.route_url('survey.run.inactive', sid=request.matchdict['sid']))
        state = init_state(request, dbsession, survey)
        if not state['qsid']:
            response = HTTPFound(request.route_url('survey.run', sid=request.matchdict['sid']))
            response.delete_cookie('survey.%s' % request.matchdict['sid'])
            raise response
        qsheet = dbsession.query(QSheet).filter(QSheet.id==safe_int(state['qsid'])).first()
        if not qsheet:
            response = HTTPFound(request.route_url('survey.run.finished', sid=request.matchdict['sid']))
            response.delete_cookie('survey.%s' % request.matchdict['sid'])
            raise response
        if request.method == 'GET':
            if 'dids' not in state:
                state['dids'] = select_data_items(request.matchdict['sid'], state, qsheet, dbsession)
                if len(state['dids']) == 0:
                    response = HTTPFound(request.route_url('survey.run', sid=request.matchdict['sid']))
                    next_qsi = next_qsheet(qsheet)
                    if next_qsi:
                        state['qsid'] = next_qsi.id
                    else:
                        state['qsid'] = 'finished'
                    del state['dids']
                    response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
                    raise response
            data_items = load_data_items(state, dbsession)
            request.response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
            return {'survey': survey,
                    'qsheet': qsheet,
                    'data_items': data_items,
                    'submit_options': determine_submit_options(qsheet)}
        elif request.method == 'POST':
            data_items = load_data_items(state, dbsession)
            validator = PageSchema(qsheet, data_items)
            try:
                qsheet_answers = validator.to_python(request.POST, ValidationState(request=request))
                with transaction.manager:
                    participant = get_participant(dbsession, survey, state)
                    for question in qsheet.questions:
                        for data_item_src in data_items:
                            data_item = dbsession.query(DataItem).filter(DataItem.id==safe_int(data_item_src['did'])).first()
                            if data_item:
                                for answer in dbsession.query(Answer).filter(and_(Answer.participant_id==participant.id,
                                                                                  Answer.question_id==question.id,
                                                                                  Answer.data_item_id==data_item.id)):
                                    dbsession.delete(answer)
                            else:
                                for answer in dbsession.query(Answer).filter(and_(Answer.participant_id==participant.id,
                                                                                    Answer.question_id==question.id)):
                                    dbsession.delete(answer)
                with transaction.manager:
                    participant = get_participant(dbsession, survey, state)
                    for question in qsheet.questions:
                        if question.type == 'text':
                            continue
                        for data_item_src in data_items:
                            data_item = None
                            data_item = dbsession.query(DataItem).filter(DataItem.id==safe_int(data_item_src['did'])).first()
                            answer = Answer(participant_id=participant.id,
                                            question_id=question.id)
                            if data_item:
                                answer.data_item_id = data_item.id
                            if question.type == 'rating_group':
                                for sub_question in get_attr_groups(question, 'subquestion'):
                                    if qsheet_answers['items'][unicode(data_item_src['did'])][question.name] and get_qg_attr_value(sub_question, 'name') in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                        answer.values.append(AnswerValue(name=get_qg_attr_value(sub_question, 'name'),
                                                                         value=qsheet_answers['items'][unicode(data_item_src['did'])][question.name][get_qg_attr_value(sub_question, 'name')]))
                                    else:
                                        answer.values.append(AnswerValue(name=get_qg_attr_value(sub_question, 'name'),
                                                                         value=None))
                            elif question.type == 'multichoice':
                                answer_list = qsheet_answers['items'][unicode(data_item_src['did'])][question.name]
                                if isinstance(answer_list, list):
                                    for value in answer_list:
                                        answer.values.append(AnswerValue(value=value))
                                else:
                                    answer.values.append(AnswerValue(value=answer_list))
                            elif question.type == 'multichoice_group':
                                for sub_question in get_attr_groups(question, 'subquestion'):
                                    print repr(qsheet_answers)
                                    if qsheet_answers['items'][unicode(data_item_src['did'])][question.name] and get_qg_attr_value(sub_question, 'name') in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                        answer_list = qsheet_answers['items'][unicode(data_item_src['did'])][question.name][get_qg_attr_value(sub_question, 'name')]
                                        if isinstance(answer_list, list):
                                            for value in answer_list:
                                                answer.values.append(AnswerValue(name=get_qg_attr_value(sub_question, 'name'),
                                                                                 value=value))
                                        else:
                                            answer.values.append(AnswerValue(name=get_qg_attr_value(sub_question, 'name'),
                                                                             value=answer_list))
                                    else:
                                        answer.values.append(AnswerValue(name=get_qg_attr_value(sub_question, 'name'),
                                                                         value=None))
                            elif question.type == 'ranking':
                                for sub_answer in get_attr_groups(question, 'answer'):
                                    if get_qg_attr_value(sub_answer, 'value') in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                        answer.values.append(AnswerValue(name=get_qg_attr_value(sub_answer, 'value'),
                                                                         value=qsheet_answers['items'][unicode(data_item_src['did'])][question.name][get_qg_attr_value(sub_answer, 'value')]))
                                    else:
                                        answer.values.append(AnswerValue(name=get_qg_attr_value(sub_answer, 'value'),
                                                                         value=None))
                            else:
                                if qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                    answer.values.append(AnswerValue(value=unicode(qsheet_answers['items'][unicode(data_item_src['did'])][question.name])))
                                else:
                                    answer.values.append(AnswerValue(value=None))
                            dbsession.add(answer)
                update_data_item_counts(state, [d['did'] for d in data_items], dbsession)
                qsheet = dbsession.query(QSheet).filter(QSheet.id==state['qsid']).first()
                if qsheet_answers['action_'] in ['Next', 'Finish']:
                    next_qsi = next_qsheet(qsheet)
                    if next_qsi:
                        state['qsid'] = next_qsi.id
                    else:
                        state['qsid'] = 'finished'
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
                        'submit_options': determine_submit_options(qsheet),
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
from pyquest.helpers.qsheet import get_attr_groups, get_qg_attr_value
from sqlalchemy.sql.expression import not_
