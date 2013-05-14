# -*- coding: utf-8 -*-
u"""
:mod:`pyquest.views.frontend`
=============================

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
from pywebtools.renderer import render
from random import sample, shuffle
from sqlalchemy import and_, asc
from sqlalchemy.sql.expression import not_

from pyquest.l10n import get_translator
from pyquest.models import (DBSession, Survey, QSheet, DataItem, Participant,
    DataItemCount, Answer, AnswerValue, Question, TransitionCondition)
from pyquest.validation import PageSchema, ValidationState, flatten_invalid
from pyquest.helpers.qsheet import transition_sorter

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

def select_data_items(qsid, state, qsheet, dbsession):
    def data_item_transform(t):
        if t[1]:
            return (t[0], t[1].count)
        else:
            return (t[0], 0)
    if not qsheet.dataset:
        return [{'did': 'none'}]
    else:
        disid = qsheet.dataset.id
        source_items = map(data_item_transform,
                           dbsession.query(DataItem, DataItemCount).\
                                outerjoin(DataItemCount).filter(and_(DataItem.data_item_set_id==disid,
                                                                     DataItem.control==False,
                                                                     not_(DataItem.id.in_(dbsession.query(Answer.data_item_id).join(Question, QSheet).filter(and_(Answer.participant_id==state['ptid'],
                                                                                                                                                                  QSheet.id==qsheet.id)))))
                                                                ).all())
        source_items.sort(key=lambda i: i[1])
        if len(source_items) > 0:
            data_items = []
            threshold = source_items[0][1]
            max_threshold = source_items[len(source_items) - 1][1]
            while len(data_items) < int(qsheet.attr_value('data-items')):
                if threshold > max_threshold:
                    return []
                threshold_items = filter(lambda t: t[1] == threshold, source_items)
                required_count = int(qsheet.attr_value('data-items')) - len(data_items)
                if required_count < len(threshold_items):
                    data_items.extend(map(lambda t: {'did': t[0].id}, sample(threshold_items, required_count)))
                else:
                    data_items.extend(map(lambda t: {'did': t[0].id}, threshold_items))
                threshold = threshold + 1
            control_items = map(lambda d: {'did': d.id},
                                dbsession.query(DataItem).filter(and_(DataItem.data_item_set_id==disid,
                                                                      DataItem.control==True)).all())
            if len(control_items) < int(qsheet.attr_value('control-items')):
                data_items.extend(control_items)
            else:
                data_items.extend(sample(control_items, int(qsheet.attr_value('control-items'))))
            shuffle(data_items)
            return data_items
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

def determine_qsheet_buttons(qsheet):
    """Determines which buttons should be shown for the qsheet.
    
    If the :py:class:`~pyquest.models.QSheet` is the last in the :py:class:`~pyquest.models.Survey`
    the return value will include 'finish' otherwise 'next'. if the :py:class:`~pyquest.models.QSheet`
    can be answered repeatedly then the return value will include 'more'. If the
    :py:class:`~pyquest.models.QSheet` has questions that require answering, then
    'clear' will be included in the return value.
    
    :param qsheet: The :py:class:`~pyquest.models.QSheet` to determine the buttons for
    :return: A `list` with the submit options
    """
    if qsheet.next and qsheet.next[0].target_id != None:
        options = ['next']
    else:
        options = ['finish']

    if qsheet.attr_value('repeat') == 'repeat':
        options.append('more')
        
    if (len([q for q in qsheet.questions if q.q_type.answer_schema()])):
        options.append('clear');

    return options

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

def next_qsheet(dbsession, qsheet, participant):
    """ Returns the next qsheet. Goes through all the transitions specified for this qsheet and looks for the first one
    which either has no condition or has a condition which is fulfilled.

    :param dbsession: a sqlalchemy data base session
    :param qsheet: The :py:class:`~pyquest.models.QSheet` we are leaving
    :param participant: The :py:class:`~pyquest.models.Participant`
    :return The next :py:class:`~pyquest.models.QSheet` or None (which means finish).
    """
    for transition in sorted(qsheet.next, key=transition_sorter, reverse=True):
        condition = dbsession.query(TransitionCondition).filter(TransitionCondition.transition_id==transition.id).first()
        if (condition == None or condition.evaluate(dbsession, participant) == True):
            return transition.target
    return None

def calculate_progress(qsheet, participant):
    def count_to_end(qsheet):
        if qsheet and qsheet.next:
            return max([count_to_end(t.target) for t in qsheet.next])
        else:
            return 1
    answered_qsids = set([a.question.qsheet.id for a in participant.answers])
    done = len(answered_qsids)
    remaining = count_to_end(qsheet)
    if qsheet.id not in answered_qsids:
        remaining = remaining + 1
    if done + remaining == 0:
        return None
    else:
        return (done, remaining)

def calculate_control_items(qsheet, participant):
    correct = 0
    total = 0
    for answer in participant.answers:
        if (not qsheet or answer.question.qsheet_id == qsheet.id) and answer.data_item and answer.data_item.control:
            total = total + 1
            if answer.values[0].value == answer.data_item.control_answers[0].answer:
                correct = correct + 1
    if total == 0:
        return None
    else:
        return (correct, total)

@view_config(route_name='survey.run')
@render({'text/html': 'frontend/qsheet.html'})
def run_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    if survey:
        _ = get_translator(survey.language, 'frontend').ugettext
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
            raise response
        if request.method == 'GET':
            if 'dids' not in state:
                state['dids'] = select_data_items(qsheet.id, state, qsheet, dbsession)
                if len(state['dids']) == 0:
                    response = HTTPFound(request.route_url('survey.run', sid=request.matchdict['sid']))
                    participant = get_participant(dbsession, survey, state)
                    next_qsi = next_qsheet(dbsession, qsheet, participant)
                    if next_qsi:
                        state['qsid'] = next_qsi.id
                    else:
                        state['qsid'] = 'finished'
                    del state['dids']
                    response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
                    raise response
            data_items = load_data_items(state, dbsession)
            participant = get_participant(dbsession, survey, state)
            request.response.set_cookie('survey.%s' % request.matchdict['sid'], pickle.dumps(state), max_age=7776000)
            dbsession.add(qsheet)
            return {'survey': survey,
                    'qsheet': qsheet,
                    'data_items': data_items,
                    'submit_options': determine_qsheet_buttons(qsheet),
                    'progress': calculate_progress(qsheet, participant),
                    'control': calculate_control_items(qsheet, participant),
                    'participant': participant}
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
                        for data_item_src in data_items:
                            data_item = dbsession.query(DataItem).filter(DataItem.id==safe_int(data_item_src['did'])).first()
                            answer = Answer(participant_id=participant.id,
                                            question_id=question.id)
                            if data_item:
                                answer.data_item_id = data_item.id
                            schema = question.q_type.answer_schema()
                            if schema:
                                if schema['type'] in ['unicode', 'int', 'month', 'date', 'time', 'datetime', 'url', 'email', 'number']:
                                    if qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                        answer_list = qsheet_answers['items'][unicode(data_item_src['did'])][question.name]
                                        if isinstance(answer_list, list):
                                            for value in answer_list:
                                                answer.values.append(AnswerValue(value=unicode(value)))
                                        else:
                                            answer.values.append(AnswerValue(value=unicode(answer_list)))
                                    else:
                                        answer.values.append(AnswerValue(value=None))
                                elif schema['type'] == 'choice':
                                    if schema['params']['allow_multiple']:
                                        answer_list = qsheet_answers['items'][unicode(data_item_src['did'])][question.name]
                                        if isinstance(answer_list, list):
                                            for value in answer_list:
                                                answer.values.append(AnswerValue(value=value))
                                        else:
                                            answer.values.append(AnswerValue(value=answer_list))
                                    else:
                                        if qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                            answer.values.append(AnswerValue(value=unicode(qsheet_answers['items'][unicode(data_item_src['did'])][question.name])))
                                        else:
                                            answer.values.append(AnswerValue(value=None))
                                elif schema['type'] == 'multiple':
                                    sub_schema = schema['schema']
                                    for attr in question.attr_value(schema['attr'], multi=True, default=[]):
                                        if sub_schema['params']['allow_multiple']:
                                            if qsheet_answers['items'][unicode(data_item_src['did'])][question.name] and attr in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                                answer_list = qsheet_answers['items'][unicode(data_item_src['did'])][question.name][attr]
                                                if isinstance(answer_list, list):
                                                    for value in answer_list:
                                                        answer.values.append(AnswerValue(name=attr, value=value))
                                                else:
                                                    answer.values.append(AnswerValue(name=attr, value=answer_list))
                                            else:
                                                answer.values.append(AnswerValue(name=attr, value=None))
                                        else:
                                            if qsheet_answers['items'][unicode(data_item_src['did'])][question.name] and attr in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                                answer.values.append(AnswerValue(name=attr, value=qsheet_answers['items'][unicode(data_item_src['did'])][question.name][attr]))
                                            else:
                                                answer.values.append(AnswerValue(name=attr, value=None))
                                elif schema['type'] == 'ranking':
                                    for attr in question.attr_value(schema['attr'], multi=True, default=[]):
                                        if attr in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                            answer.values.append(AnswerValue(name=attr, value=qsheet_answers['items'][unicode(data_item_src['did'])][question.name][attr]))
                                        else:
                                            answer.values.append(AnswerValue(name=attr, value=None))
                                dbsession.add(answer)
                update_data_item_counts(state, [d['did'] for d in data_items], dbsession)
                qsheet = dbsession.query(QSheet).filter(QSheet.id==state['qsid']).first()
                if qsheet_answers['action_'] in [_('Next Page'), _('Finish Survey')]:
                    participant = get_participant(dbsession, survey, state)
                    next_qsi = next_qsheet(dbsession, qsheet, participant)
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
                participant = get_participant(dbsession, survey, state)
                dbsession.add(qsheet)
                return {'survey': survey,
                        'qsheet': qsheet,
                        'data_items': data_items,
                        'submit_options': determine_qsheet_buttons(qsheet),
                        'progress': calculate_progress(qsheet, participant),
                        'control': calculate_control_items(qsheet, participant),
                        'participant': participant,
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
        return {'survey': survey,
                'control': calculate_control_items(None, get_participant(dbsession, survey, init_state(request, dbsession, survey)))}
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
