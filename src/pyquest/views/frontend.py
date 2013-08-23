# -*- coding: utf-8 -*-
u"""
:mod:`pyquest.views.frontend`
=============================

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import transaction

from beaker.session import SessionObject
from beaker.util import coerce_session_params
from formencode import api
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pywebtools.renderer import render
from random import sample, shuffle, random
from sqlalchemy import and_
from sqlalchemy.sql.expression import not_

from pyquest.l10n import get_translator
from pyquest.models import (DBSession, Survey, QSheet, DataItem, Participant,
    DataItemCount, Answer, AnswerValue, Question, TransitionCondition, DataSet, DataSetAttributeKey, DataItemAttribute, PermutationSet)
from pyquest.validation import PageSchema, ValidationState, flatten_invalid
from pyquest.helpers.qsheet import transition_sorter
import json

class ParticipantManager(object):
    
    def __init__(self, request, dbsession, survey):
        session = SessionObject(request.environ, **coerce_session_params({'type':'cookie',
                                                                        'cookie_expires': 7776000,
                                                                        'key': 'survey.%s' % (survey.external_id),
                                                                        'encrypt_key': 'thisisatest',
                                                                        'validate_key': 'testing123',
                                                                        'auto': True}))
        self._request = request
        self._dbsession = dbsession
        self._survey = survey
        self._participant = None
        if 'participant_id' in session:
            self._participant = dbsession.query(Participant).filter(Participant.id==session['participant_id']).first()
        if not self._participant:
            with transaction.manager:
                self._participant = Participant(survey_id=survey.id)
                dbsession.add(self._participant)
                dbsession.flush()
                ps = dbsession.query(PermutationSet).filter(PermutationSet.survey_id==survey.id).first()
                pds = ps.assign_next_permutation(self._participant)
                dbsession.flush()
            dbsession.add(self._participant)
            session['participant_id'] = self._participant.id
            session.persist()
            request.response.headerlist.append(('Set-Cookie', session.__dict__['_headers']['cookie_out']))
        else:
            if request.url.endswith('finished') and self._participant.permutation_id:
                with transaction.manager:
                    pds = dbsession.query(DataSet).filter(DataSet.id==self._participant.permutation_id).first()
                    dbsession.delete(pds)
                    self._participant.permutation_id = None
                    dbsession.flush()

    def state(self):
        self._dbsession.add(self._participant)
        self._dbsession.add(self._survey)
        state = self._participant.get_state()
        if not state:
            state = {}
        if 'current-qsheet' not in state:
            state['current-qsheet'] = self._survey.start.id
        if 'history' not in state:
            state['history'] = []
        if 'data-items' not in state:
            state['data-items'] = {}
        self._participant.set_state(state)
        return state
    
    def current_qsheet(self):
        state = self.state()
        if state['current-qsheet'] != '_finished':
            return self._dbsession.query(QSheet).filter(QSheet.id==state['current-qsheet']).first()
        else:
            return None
    
    def participant(self):
        self._dbsession.add(self._participant)
        return self._participant
    
    def current_data_items(self):
        def data_item_transform(t):
            if t[1]:
                return (t[0], t[1].count)
            else:
                return (t[0], 0)
        state = self.state()
        qsheet = self.current_qsheet()
        self.data_set_in_use = None
        pds = None
        if self._participant.permutation_id and str(qsheet.id) in self._participant.permutation_qsheet_id.split(','):
            pds = self._dbsession.query(DataSet).filter(DataSet.id==self._participant.permutation_id).first()
        if pds:
            self.data_set_in_use = pds
            do_sample = False
        else:
            self.data_set_in_use = qsheet.data_set
            do_sample = True
        if self.data_set_in_use:
            dsid = unicode(self.data_set_in_use.id)
            if dsid not in state['data-items']:
                state['data-items'][dsid] = {'seen': []}
            if 'current' not in state['data-items'][dsid]:
                item_count = int(qsheet.attr_value('data-items', default='0'))
                control_count = int(qsheet.attr_value('control-items', default='0'))
                source_items = map(data_item_transform,
                                   self._dbsession.query(DataItem, DataItemCount).\
                                       outerjoin(DataItemCount).filter(and_(DataItem.dataset_id==self.data_set_in_use.id,
                                                                            DataItem.control==False,
                                                                            not_(DataItem.id.in_(self._dbsession.query(Answer.data_item_id).join(Question, QSheet).filter(and_(Answer.participant_id==self._participant.id,
                                                                                                                                                                               QSheet.id==qsheet.id)))))
                                                                       ).all())
                source_items.sort(key=lambda i: i[1])
                data_items = []
                if len(source_items) > 0:
                    threshold = source_items[0][1]
                    max_threshold = source_items[len(source_items) - 1][1]
                    while len(data_items) < item_count:
                        if threshold > max_threshold:
                            return None
                        threshold_items = filter(lambda t: t[1] == threshold, source_items)
                        required_count = item_count - len(data_items)
                        if required_count < len(threshold_items):
                            if do_sample:
                                data_items.extend(map(lambda t: t[0].id, sample(threshold_items, required_count)))
                            else:
                                data_items.extend(map(lambda t: t[0].id, threshold_items[:required_count]))
                        else:
                            data_items.extend(map(lambda t: t[0].id, threshold_items))
                        threshold = threshold + 1
                if len(source_items) < item_count:
                    return None
                control_items = map(lambda d: d.id,
                                    self._dbsession.query(DataItem).filter(and_(DataItem.dataset_id==self.data_set_in_use.id,
                                                                          DataItem.control==True)).all())
                if len(control_items) < control_count:
                    data_items.extend(control_items)
                else:
                    data_items.extend(sample(control_items, control_count))
                shuffle(data_items)
                state['data-items'][dsid]['current'] = data_items
                self.participant().set_state(state)
            else:
                data_items = state['data-items'][dsid]['current']
            current_items = []
            for did in data_items:
                data_item = self._dbsession.query(DataItem).filter(DataItem.id==did).first()
                data_item_data = {'did': data_item.id}
                for attr in data_item.attributes:
                    data_item_data[attr.key.key] = attr.value
                current_items.append(data_item_data)
            return current_items
        else:
            return [{'did': 'none'}]
    
    def next_qsheet(self, params):
        next_qs = None
        transition = None
        for transition in sorted(self.current_qsheet().next, key=transition_sorter, reverse=True):
            condition = self._dbsession.query(TransitionCondition).filter(TransitionCondition.transition_id==transition.id).first()
            if (condition == None or condition.evaluate(self._dbsession, self.participant()) == True):
                transition = transition
                if transition.target:
                    next_qs = transition.target
                    break
        action = 'next'
        if params['action_'] == 'More Questions':
            action = 'more'
        elif params['action_'] == 'Next Page':
            action = 'next'
        elif params['action_'] == 'Finish Survey':
            action = 'finish'
        state = self.state()
        state['history'].append(self.current_qsheet().id)
        if action == 'finish':
            state['current-qsheet'] = '_finished'
        elif action == 'next':
            if next_qs:
                if next_qs.id in state['history'] and next_qs.data_set:
                    dsid = unicode(next_qs.data_set.id)
                    if dsid in state['data-items'] and 'current' in state['data-items'][dsid]:
                        del state['data-items'][dsid]['current']
                state['current-qsheet'] = next_qs.id
            elif transition:
                state['current-qsheet'] = '_finished'
        elif action == 'more':
            if self.data_set_in_use:
                dsid = unicode(self.data_set_in_use.id)
                if dsid in state['data-items'] and 'current' in state['data-items'][dsid]:
                    del state['data-items'][dsid]['current']
        self._participant.set_state(state)
        return next
    
    def progress(self):
        def count_to_end(qsheet, seen = []): # TODO: Cycle detection
            seen.append(qsheet.id)
            if qsheet and qsheet.next:
                followers = [count_to_end(t.target, seen) for t in qsheet.next if t.target and t.target.id not in seen]
                if followers:
                    return max(followers) + 1
                else:
                    return 0
            else:
                return 0
        state = self.state()
        return (len(state['history']) + 1, len(state['history']) + count_to_end(self.current_qsheet()))
    
    def control_score(self):
        correct = 0
        total = 0
        qsheet = self.current_qsheet()
        for answer in self.participant().answers:
            if (not qsheet or answer.question.qsheet_id == qsheet.id) and answer.data_item and answer.data_item.control:
                total = total + 1
                if answer.values[0].value == answer.data_item.control_answers[0].answer:
                    correct = correct + 1
        if total == 0:
            return None
        else:
            return (correct, total)

@view_config(route_name='survey.run')
@render({'text/html': 'frontend/running.html'})
def run_survey(request):
    def safe_int(value):
        try:
            return int(value)
        except ValueError:
            return None
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.external_id==request.matchdict['seid']).first()
    if survey:
        _ = get_translator(survey.language, 'frontend').ugettext
        if survey.status not in ['running', 'testing']:
            raise HTTPFound(request.route_url('survey.run.inactive', seid=request.matchdict['seid']))
        part_manager = ParticipantManager(request, dbsession, survey)
        if part_manager.state()['current-qsheet'] == '_finished':
            raise HTTPFound(request.route_url('survey.run.finished', seid=request.matchdict['seid']))
        with transaction.manager:
            qsheet = part_manager.current_qsheet()
            data_items = part_manager.current_data_items()
        qsheet = part_manager.current_qsheet()
        data_items = part_manager.current_data_items()
        if not data_items:
            with transaction.manager:
                request.session.flash('There are no more questions to answer in this section', queue='info')
                part_manager.next_qsheet({'action_': 'Next Page'})
            raise HTTPFound(request.route_url('survey.run.finished', seid=request.matchdict['seid']))
        if request.method == 'GET':
            return {'survey': survey,
                    'qsheet': qsheet,
                    'data_items': data_items,
                    'submit_options': qsheet.valid_buttons(),
                    'progress': part_manager.progress(),
                    'control': part_manager.control_score(),
                    'participant': part_manager.participant()}
        elif request.method == 'POST':
            try:
                validator = PageSchema(qsheet, data_items)
                qsheet_answers = validator.to_python(request.POST, ValidationState(request=request)) # TODO: Should check that the _action parameter is valid
                participant = part_manager.participant()
                with transaction.manager:
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
                participant = part_manager.participant()
                with transaction.manager:
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
                    for did in [d['did'] for d in data_items]:
                        if did != 'none':
                            count = dbsession.query(DataItemCount).filter(and_(DataItemCount.data_item_id==did,
                                                                               DataItemCount.qsheet_id==qsheet.id)).first()
                            if count:
                                count.count = count.count + 1
                            else:
                                dbsession.add(DataItemCount(data_item_id=did, qsheet_id=qsheet.id, count=1))
                    part_manager.next_qsheet(qsheet_answers)
            except api.Invalid as e:
                e = flatten_invalid(e)
                e.params = request.POST
                return {'survey': survey,
                        'qsheet': qsheet,
                        'data_items': data_items,
                        'submit_options': qsheet.valid_buttons(),
                        'progress': part_manager.progress(),
                        'control': part_manager.control_score(),
                        'participant': part_manager.participant(),
                        'e': e}
            dbsession.add(survey)
            raise HTTPFound(request.route_url('survey.run', seid=survey.external_id))
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.run.finished')
@render({'text/html': 'frontend/finished.html'})
def finished_survey(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.external_id==request.matchdict['seid']).first()
    if survey:
        part_manager = ParticipantManager(request, dbsession, survey)
        dbsession.add(survey)
        if survey.status == 'testing':
            request.response.delete_cookie('survey.%s' % request.matchdict['seid'])
        return {'survey': survey,
                'control': part_manager.control_score()}
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.run.inactive')
@render({'text/html': 'frontend/inactive.html'})
def inactive(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.external_id==request.matchdict['seid']).first()
    if survey:
        if survey.status in ['running', 'testing']:
            raise HTTPFound(request.route_url('survey.run', seid=request.matchdict['seid']))
        elif survey.status == 'develop':
            raise HTTPNotFound()
        return {'survey': survey}
    else:
        raise HTTPNotFound()
