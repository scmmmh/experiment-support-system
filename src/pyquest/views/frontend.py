# -*- coding: utf-8 -*-
u"""
:mod:`pyquest.views.frontend`
=============================

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json
import transaction

from beaker.session import SessionObject
from beaker.util import coerce_session_params
from formencode import api
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pywebtools.renderer import render
from random import sample, choice, shuffle
from sqlalchemy import and_
from sqlalchemy.sql.expression import not_

from pyquest.l10n import get_translator
from pyquest.models import (DBSession, Survey, QSheet, DataItem, Participant,
    DataItemCount, Answer, AnswerValue, Question)
from pyquest.validation import PageSchema, ValidationState, flatten_invalid
from pyquest.util import get_config_setting

class ParticipantManager(object):
    
    def __init__(self, request, dbsession, survey):
        
        session = SessionObject(request.environ, **coerce_session_params({'type':'cookie',
                                                                        'cookie_expires': 7776000,
                                                                        'key': 'survey.%s' % (survey.external_id),
                                                                        'encrypt_key': get_config_setting(request, 'beaker.session.encrypt_key'),
                                                                        'validate_key': get_config_setting(request, 'beaker.session.validate_key'),
                                                                        'auto': True}))
        self._request = request
        self._dbsession = dbsession
        self._survey = survey
        self._participant = None
        if 'participant_id' in session:
            self._participant = dbsession.query(Participant).filter(Participant.id==session['participant_id']).first()
        if not self._participant:
            with transaction.manager:
                dbsession.add(self._survey)
                self._participant = Participant(survey_id=survey.id)
                permutation_items = {}
                for qsheet in self._survey.qsheets:
                    if qsheet.data_set and qsheet.data_set.type == 'permutationset':
                        pairs = dbsession.query(DataItem, Participant).outerjoin(Participant, DataItem.id==Participant.permutation_item_id).filter(DataItem.dataset_id==qsheet.data_set.id)
                        if pairs.count() > 0:
                            items = {}
                            # Weighted random sampling, but only using those participants who have completed 
                            for pair in pairs:
                                if pair[1] and pair[1].completed:
                                    if pair[0].id in items:
                                        items[pair[0].id] = (pair[0], items[pair[0].id][1] + 1)
                                    else:
                                        items[pair[0].id] = (pair[0], 1)
                                else:
                                    items[pair[0].id] = (pair[0], 0)
                            items = items.values()
                            max_count = max([item[1] for item in items]) + 1
                            weighted_items = []
                            for item, cnt in items:
                                weighted_items.extend([item for _ in range(0, max_count - cnt)])
                            item = choice(weighted_items)
                            
                            # Load chosen permutation data
                            self._participant.permutation_item = item
                            items = []
                            for idx, data in enumerate(json.loads(item.attributes[0].value)):
                                data['did'] = item.id
                                data['_sub_did'] = idx
                                items.append(data)
                            permutation_items[unicode(qsheet.data_set.id)] = items    
                            permutation_items[unicode(qsheet.data_set.id)].reverse()
                pages = {}
                start_id = self.build_pages(self._survey.start, pages, {'permutation-items': permutation_items})
                self._participant.set_state({'pages': pages,
                                             'current-page': start_id,
                                             'history': [],
                                             'data-items': {},
                                             'permutation-items': permutation_items})
                dbsession.add(self._participant)
                dbsession.flush()
            dbsession.add(self._participant)
            session['participant_id'] = self._participant.id
            session.persist()
            request.response.headerlist.append(('Set-Cookie', session.__dict__['_headers']['cookie_out']))

    def build_pages(self, qsheet, pages, params):
        page_id = 0
        while unicode(page_id) in pages:
            page_id = page_id + 1
        page_id = unicode(page_id)
        page = {'qsheet': qsheet.id}
        if qsheet.data_set:
            if qsheet.data_set.type == 'dataset':
                page['data-set'] = qsheet.data_set.id
            elif qsheet.data_set.type == 'permutationset' and unicode(qsheet.data_set.id) in params['permutation-items']:
                page['data-items'] = [params['permutation-items'][unicode(qsheet.data_set.id)][-1]]
        pages[page_id] = page
        if qsheet.next:
            page['next'] = []
            for transition in qsheet.next:
                if transition.target:
                    if transition.condition:
                        if transition.condition['type'] == 'permutation':
                            permutation = [perm for perm in qsheet.survey.permutation_sets if perm.name==transition.condition['permutation']]
                            if permutation and unicode(permutation[0].id) in params['permutation-items'] and len(params['permutation-items'][unicode(permutation[0].id)]) > 1:
                                params['permutation-items'][unicode(permutation[0].id)].pop()
                                next_id = self.build_pages(transition.target, pages, params)
                                page['next'].append({'page': next_id})
                                pages[next_id]['prev'] = page_id
                        else:
                            # TODO: Detect and stop cycles
                            next_id = self.build_pages(transition.target, pages, params)
                            page['next'].append({'page': next_id,
                                                 'condition': transition.condition})
                            pages[next_id]['prev'] = page_id
                    else:
                        next_id = self.build_pages(transition.target, pages, params)
                        page['next'].append({'page': next_id})
                        pages[next_id]['prev'] = page_id
        return page_id
    
    def state(self):
        self._dbsession.add(self._participant)
        self._dbsession.add(self._survey)
        state = self._participant.get_state()
        return state
    
    def current_qsheet(self):
        state = self.state()
        if state['current-page'] != '_finished':
            return self._dbsession.query(QSheet).filter(QSheet.id==state['pages'][state['current-page']]['qsheet']).first()
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
        if 'data-set' in state['pages'][state['current-page']]:
            dsid = unicode(state['pages'][state['current-page']]['data-set'])
            if dsid not in state['data-items']:
                state['data-items'][dsid] = {'seen': []}
            if 'current' not in state['data-items'][dsid]:
                item_count = int(qsheet.attr_value('data-items', default='0'))
                control_count = int(qsheet.attr_value('control-items', default='0'))
                source_items = map(data_item_transform,
                                   self._dbsession.query(DataItem, DataItemCount).\
                                       outerjoin(DataItemCount).filter(and_(DataItem.dataset_id==qsheet.data_set.id,
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
                            data_items.extend(map(lambda t: t[0].id, sample(threshold_items, required_count)))
                        else:
                            data_items.extend(map(lambda t: t[0].id, threshold_items))
                        threshold = threshold + 1
                if len(source_items) < item_count:
                    return None
                control_items = map(lambda d: d.id,
                                    self._dbsession.query(DataItem).filter(and_(DataItem.dataset_id==qsheet.data_set.id,
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
        elif 'data-items' in state['pages'][state['current-page']]:
            return state['pages'][state['current-page']]['data-items']
        else:
            return [{'did': 'none'}]
    
    def next_qsheet(self, params):
        state = self.state()
        page = state['pages'][state['current-page']]
        state['history'].append(page)
        if params['action_'] == 'More Questions':
            if self.current_qsheet().data_set:
                dsid = unicode(self.current_qsheet().data_set.id)
                if dsid in state['data-items'] and 'current' in state['data-items'][dsid]:
                    del state['data-items'][dsid]['current']
        else:
            next_id = None
            if 'next' in page:
                for transition in page['next']:
                    if 'condition' in transition:
                        condition = transition['condition']
                        if condition['type'] == 'answer':
                            question = [q for qs in self._survey.qsheets for q in qs.questions if '%s.%s' % (qs.name, q.name) == condition['question']]
                            if question:
                                answer = self._dbsession.query(Answer).filter(and_(Answer.participant_id==self.participant().id,
                                                                                   Answer.question_id==question[0].id)).first()
                                if answer:
                                    for value in answer.values:
                                        if value.value == condition['answer']:
                                            next_id = transition['page']
                                            break
                    else:
                        next_id = transition['page']
                        break
            if next_id:
                state['current-page'] = next_id
            else:
                state['current-page'] = '_finished'
        self.participant().set_state(state)
    
    def progress(self):
        def count_to_end(page_id, pages, seen=[]):
            seen.append(page_id)
            if 'next' in pages[page_id]:
                counts = []
                has_next = False
                for transition in pages[page_id]['next']:
                    if transition['page'] not in seen and transition['page'] != page_id:
                        counts.append(count_to_end(transition['page'], pages, seen + [page_id]))
                        has_next = True
                if has_next:
                    return max(counts) + 1
                else:
                    return 1
            else:
                return 1
        state = self.state()
        return (len(state['history']) + 1, len(state['history']) + count_to_end(state['current-page'], state['pages']))
    
    def control_score(self):
        correct = 0
        total = 0
        qsheet = self.current_qsheet()
        for answer in self.participant().answers:
            if (not qsheet or answer.question.qsheet_id == qsheet.id) and answer.data_item and answer.data_item.control:
                total = total + 1
                matches = False
                for answer_value in answer.values:
                    for control_answer in answer.data_item.control_answers:
                        if answer_value.value == control_answer.answer:
                            matches = True
                            break
                if matches:
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
        if part_manager.state()['current-page'] == '_finished':
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
                            if '_sub_did' in data_item_src and data_item:
                                query = dbsession.query(AnswerValue).join(Answer).filter(and_(Answer.participant_id==participant.id,
                                                                                                                        Answer.question_id==question.id,
                                                                                                                        Answer.data_item_id==data_item.id,
                                                                                                                        AnswerValue.name.startswith(unicode(data_item_src['_sub_did']))))
                            else:
                                query = dbsession.query(Answer)
                                if data_item:
                                    query = query.filter(and_(Answer.participant_id==participant.id,
                                                              Answer.question_id==question.id,
                                                              Answer.data_item_id==data_item.id))
                                else:
                                    query = query.filter(and_(Answer.participant_id==participant.id,
                                                              Answer.question_id==question.id))
                            for answer in query:
                                print 'Deleting!'
                                dbsession.delete(answer)
                participant = part_manager.participant()
                with transaction.manager:
                    for question in qsheet.questions:
                        for data_item_src in data_items:
                            data_item = dbsession.query(DataItem).filter(DataItem.id==safe_int(data_item_src['did'])).first()
                            if '_sub_did' in data_item_src:
                                sub_data_item = data_item_src['_sub_did']
                                answer = dbsession.query(Answer).filter(Answer.participant_id==participant.id,
                                                                        Answer.question_id==question.id,
                                                                        Answer.data_item_id==data_item.id).first()
                            else:
                                answer = None
                                sub_data_item = None
                            if not answer:
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
                                                answer.values.append(AnswerValue(name=sub_data_item, value=unicode(value)))
                                        else:
                                            answer.values.append(AnswerValue(name=sub_data_item, value=unicode(answer_list)))
                                    else:
                                        answer.values.append(AnswerValue(name=sub_data_item, value=None))
                                elif schema['type'] == 'choice':
                                    if schema['params']['allow_multiple']:
                                        answer_list = qsheet_answers['items'][unicode(data_item_src['did'])][question.name]
                                        if isinstance(answer_list, list):
                                            for value in answer_list:
                                                answer.values.append(AnswerValue(name=sub_data_item, value=value))
                                        else:
                                            answer.values.append(AnswerValue(name=sub_data_item, value=answer_list))
                                    else:
                                        if qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                            answer.values.append(AnswerValue(name=sub_data_item, value=unicode(qsheet_answers['items'][unicode(data_item_src['did'])][question.name])))
                                        else:
                                            answer.values.append(AnswerValue(name=sub_data_item, value=None))
                                elif schema['type'] == 'multiple':
                                    sub_schema = schema['schema']
                                    for attr in question.attr_value(schema['attr'], multi=True, default=[]):
                                        if sub_schema['params']['allow_multiple']:
                                            if qsheet_answers['items'][unicode(data_item_src['did'])][question.name] and attr in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                                answer_list = qsheet_answers['items'][unicode(data_item_src['did'])][question.name][attr]
                                                if isinstance(answer_list, list):
                                                    for value in answer_list:
                                                        answer.values.append(AnswerValue(name='%s.%s' % (sub_data_item, attr) if sub_data_item != None else attr, value=value))
                                                else:
                                                    answer.values.append(AnswerValue(name='%s.%s' % (sub_data_item, attr) if sub_data_item != None else attr, value=answer_list))
                                            else:
                                                answer.values.append(AnswerValue(name='%s.%s' % (sub_data_item, attr) if sub_data_item != None else attr, value=None))
                                        else:
                                            if qsheet_answers['items'][unicode(data_item_src['did'])][question.name] and attr in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                                answer.values.append(AnswerValue(name='%s.%s' % (sub_data_item, attr) if sub_data_item != None else attr, value=qsheet_answers['items'][unicode(data_item_src['did'])][question.name][attr]))
                                            else:
                                                answer.values.append(AnswerValue(name='%s.%s' % (sub_data_item, attr) if sub_data_item != None else attr, value=None))
                                elif schema['type'] == 'ranking':
                                    for attr in question.attr_value(schema['attr'], multi=True, default=[]):
                                        if attr in qsheet_answers['items'][unicode(data_item_src['did'])][question.name]:
                                            answer.values.append(AnswerValue(name='%s.%s' % (sub_data_item, attr) if sub_data_item != None else attr, value=qsheet_answers['items'][unicode(data_item_src['did'])][question.name][attr]))
                                        else:
                                            answer.values.append(AnswerValue(name='%s.%s' % (sub_data_item, attr) if sub_data_item != None else attr, value=None))
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
        with transaction.manager:
            part_manager.participant().completed = True
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
