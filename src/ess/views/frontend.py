"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import formencode
import transaction

from beaker.session import SessionObject
from beaker.util import coerce_session_params
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pywebtools.formencode import State
from pywebtools.pyramid.util import get_config_setting 
from pywebtools.sqlalchemy import DBSession
from random import sample
from sqlalchemy import and_, func, asc

from ess.models import (Experiment, Page, Participant, Question, Answer, DataItem,
    DataSet)
from ess.validators import FrontendPageSchema


def init(config):
    config.add_route('experiment.run', '/run/{ueid}')
    config.add_route('experiment.completed', '/run/{ueid}/complete')


def remaining_pages(page, seen=None):  # Todo: Make this latin-square aware
    if seen is None:
        seen = []
    if page.id in seen:
        return (1, None)
    else:
        pages = (None, 0)
        for successor in page.next:
            if successor.target:
                next_pages = remaining_pages(successor.target, seen + [successor.target.id])
                if pages[0] is None or pages[0] > next_pages[0]:
                    pages = (next_pages[0], pages[1])
                if pages[1] is not None and next_pages[1] is not None and pages[1] < next_pages[1]:
                    pages = (pages[0], next_pages[1])
        if pages[0] is None:
            pages = (1, pages[1])
        else:
            pages = (pages[0] + 1, pages[1])
        if pages[1] is not None:
            pages = (pages[0], pages[1] + 1)
        return pages


def current_participant(request, dbsession, experiment, allow_create=True):
    """Get the current Participant or create a new one."""
    session = SessionObject(request.environ, **coerce_session_params({'type':'cookie',
                                                                      'cookie_expires': 7776000,
                                                                      'key': 'experiment.%s' % (experiment.external_id),
                                                                      'encrypt_key': get_config_setting(request, 'beaker.session.encrypt_key'),
                                                                      'validate_key': get_config_setting(request, 'beaker.session.validate_key'),
                                                                      'auto': True}))
    if 'pid' in session:
        participant = dbsession.query(Participant).filter(and_(Participant.id == session['pid'],
                                                               Participant.experiment_id == experiment.id)).first()
    else:
        participant = None
    if participant is None:
        if allow_create:
            participant = Participant(experiment_id=experiment.id,
                                      completed=False)
            participant['current'] = experiment.start.id
            participant['answered'] = []
            dbsession.add(participant)
            dbsession.flush()
        else:
            return None
    session['pid'] = participant.id
    session.persist()
    request.response.headerlist.append(('Set-Cookie', session.__dict__['_headers']['cookie_out']))
    return participant


def determine_progress(participant, page):
    answered = len(participant['answered'])
    if page is None:
        return [answered, answered, answered, answered]
    pages = remaining_pages(page)
    if pages[1] is None:
        return [answered,
                answered + pages[0],
                answered + pages[0],
                None]
    else:
        return [answered,
                answered + pages[1],
                answered + pages[0],
                answered + pages[1]]


def next_page(dbsession, participant, page, action):
    if page.next:
        for transition in page.next:
            if transition.target:
                if 'condition' in transition:
                    if transition['condition']['type'] == 'answer':
                        question = dbsession.query(Question).filter(and_(Question.id == transition['condition']['question'],
                                                                         Question.page_id == transition['condition']['page'])).first()
                        answer = dbsession.query(Answer).filter(and_(Answer.question_id == transition['condition']['question'],
                                                                     Answer.participant_id == participant.id)).first()
                        if question and answer:
                            answer = answer['response']
                            if isinstance(answer, list) and transition['condition']['value'] in answer:
                                return transition.target.id
                            elif isinstance(answer, dict) and transition['condition']['subquestion'] in answer and str(answer[transition['condition']['subquestion']]) == transition['condition']['value']:
                                return transition.target.id
                            elif str(answer) == transition['condition']['value']:
                                return transition.target.id
                    elif transition['condition']['type'] == 'dataset':
                        if page.dataset_id is not None:
                            if str(page.dataset_id) in participant['data']:
                                del participant['data'][str(page.dataset_id)]
                            data_items = select_data_items(dbsession, participant, page)
                            if data_items and action == 'more-items':
                                return transition.target.id
                    elif transition['condition']['type'] == 'latinsquare':
                        if page.dataset_id is not None:
                            if str(page.dataset_id) in participant['data']:
                                participant['data'][str(page.dataset_id)]['seen'].append(participant['data'][str(page.dataset_id)]['iids'][0])
                                participant['data'][str(page.dataset_id)]['iids'] = participant['data'][str(page.dataset_id)]['iids'][1:]
                                if len(participant['data'][str(page.dataset_id)]['iids']) > 0:
                                    return transition.target.id
                else:
                    return transition.target.id
    return None


def flatten_errors(errors):
    result = []
    if isinstance(errors, dict):
        for k, v in errors.items():
            if isinstance(v, dict):
                tmp = flatten_errors(v)
                for (sub_k, sub_v) in tmp.items():
                    result.append(('%s.%s' % (k, sub_k), sub_v))
            else:
                result.append((k, v))
    else:
        result.append(('_', errors))
    return dict(result)


def select_data_items(dbsession, participant, page):
    if 'data' not in participant:
        participant['data'] = {}
    if page is not None:
        if page.dataset_id is None:
            return [DataItem(id=None)]
        else:
            data_set = dbsession.query(DataSet).filter(DataSet.id == page.dataset_id).first()
            if data_set.type == 'dataset':
                if str(page.dataset_id) not in participant['data']:
                    data_items = dbsession.query(DataItem.id, func.count(Answer.id).label('count')).outerjoin(Answer).filter(DataItem.dataset_id == page.dataset_id).group_by(DataItem.id).order_by(asc('count'), DataItem.id)
                    seen_items = [t[0] for t in dbsession.query(DataItem.id).join(Answer).join(Participant).filter(Participant.id == participant.id)]
                    item_ids = []
                    limit_count = None
                    for item_id, count in data_items:
                        if item_id not in seen_items:
                            if limit_count is not None and limit_count != count and len(item_ids) > page['data']['item_count']:
                                break
                            item_ids.append(item_id)
                            limit_count = count
                    if item_ids and len(item_ids) >= page['data']['item_count']:
                        participant['data'][str(page.dataset_id)] = sample(item_ids, page['data']['item_count'])
                    else:
                        participant['data'][str(page.dataset_id)] = None
                        return None
                return dbsession.query(DataItem).filter(DataItem.id.in_(participant['data'][str(page.dataset_id)]))
            elif data_set.type == 'latinsquare':
                if str(page.dataset_id) not in participant['data']:
                    dids = [c[0] for c in data_set['combinations']]
                    data_items = dbsession.query(DataItem.id, func.count(Answer.id).label('count')).outerjoin(Answer).filter(and_(DataItem.dataset_id == page.dataset_id,
                                                                                                                                  DataItem.id.in_(dids))).group_by(DataItem.id).order_by(asc('count'), DataItem.id)
                    item_ids = []
                    limit_count = None
                    for item_id, count in data_items:
                        if limit_count is not None and limit_count != count and len(item_ids) > 1:
                            break
                        item_ids.append(item_id)
                        limit_count = count
                    if item_ids:
                        iid = sample(item_ids, 1)[0]
                        for combination in data_set['combinations']:
                            if combination[0] == iid:
                                participant['data'][str(page.dataset_id)] = {'iids': combination,
                                                                             'seen': []}
                                break
                    else:
                        participant['data'][str(page.dataset_id)] = None
                        return None
                return dbsession.query(DataItem).filter(DataItem.id == participant['data'][str(page.dataset_id)]['iids'][0])
            else:
                return [DataItem(id=None)]


def page_actions(participant, page):
    if page:
        actions = [('next-page', 'Next Page')]
        for transition in page.next:
            if 'condition' in transition:
                if transition['condition']['type'] == 'dataset':
                    actions.append(('more-items', 'Answer more Questions'))
        return actions
    else:
        return []


@view_config(route_name='experiment.run', renderer='ess:templates/frontend/frontend.kajiki')
def run_survey(request):
    dbsession = DBSession
    with transaction.manager:
        experiment = dbsession.query(Experiment).filter(Experiment.external_id == request.matchdict['ueid']).first()
        if experiment is None:
            raise HTTPNotFound()
        participant = current_participant(request, dbsession, experiment)
        page = dbsession.query(Page).filter(and_(Page.id == participant['current'],
                                                 Page.experiment_id == experiment.id)).first()
        data_items = select_data_items(dbsession, participant, page)
        participant['progress'] = determine_progress(participant, page)
        actions = page_actions(participant, page)
    if page is None:
        if participant['current'] is None:
            dbsession.add(experiment)
            raise HTTPFound(request.route_url('experiment.completed', ueid=experiment.external_id))
        else:
            raise HTTPNotFound()
    if request.method == 'POST':
        try:
            with transaction.manager:
                dbsession.add(experiment)
                dbsession.add(page)
                dbsession.add(participant)
                params = FrontendPageSchema(page.questions, data_items, [a[0] for a in actions]).to_python(request.params, State(request=request))
                # UserAgent Settings
                if 'user_agent' not in participant:
                    participant['user_agent'] = {}
                if 'input_type' in params['_user_agent']:
                    if 'input_types' not in participant['user_agent']:
                        participant['user_agent']['input_types'] = []
                    participant['user_agent']['input_types'] = list(set(participant['user_agent']['input_types'] + params['_user_agent']['input_type']))
                if 'screen_size' in params['_user_agent'] and params['_user_agent']['screen_size']:
                    participant['user_agent']['screen_size'] = params['_user_agent']['screen_size']
                # Experiment Responses
                for data_item in data_items:
                    for question in page.questions:
                        if question['frontend', 'display_as'] != 'text':
                            answer = Answer(participant_id=participant.id,
                                            question_id=question.id,
                                            data_item_id=data_item.id if data_item.id != -1 else None)
                            answer['response'] = params['d%s' % data_item.id][question['name']]
                            if isinstance(answer['response'], list) and len(question['frontend', 'answers']) == 1:
                                answer['response'] = answer['response'][0]
                            dbsession.add(answer)
                participant['answered'].append(page.id)
                participant['current'] = next_page(dbsession, participant, page, params['_action'])
            dbsession.add(experiment)
            raise HTTPFound(request.route_url('experiment.run', ueid=experiment.external_id))
        except formencode.Invalid as e:
            dbsession.add(experiment)
            dbsession.add(page)
            dbsession.add(participant)
            return {'experiment': experiment,
                    'page': page,
                    'participant': participant,
                    'data_items': data_items,
                    'actions': actions,
                    'values': request.params,
                    'errors': e.unpack_errors()}
    dbsession.add(experiment)
    dbsession.add(page)
    dbsession.add(participant)
    return {'experiment': experiment,
            'page': page,
            'participant': participant,
            'data_items': data_items,
            'actions': actions}


@view_config(route_name='experiment.completed', renderer='ess:templates/frontend/completed.kajiki')
def completed_survey(request):
    dbsession = DBSession
    with transaction.manager:
        experiment = dbsession.query(Experiment).filter(Experiment.external_id == request.matchdict['ueid']).first()
        participant = current_participant(request, dbsession, experiment, allow_create=False)
        if participant is None:
            raise HTTPFound(request.route_url('experiment.run', ueid=experiment.external_id))
        participant.completed = True
    dbsession.add(experiment)
    dbsession.add(participant)
    if experiment.status == 'develop':
        session = SessionObject(request.environ, **coerce_session_params({'type':'cookie',
                                                                          'cookie_expires': 7776000,
                                                                          'key': 'experiment.%s' % (experiment.external_id),
                                                                          'encrypt_key': get_config_setting(request, 'beaker.session.encrypt_key'),
                                                                          'validate_key': get_config_setting(request, 'beaker.session.validate_key'),
                                                                          'auto': True}))
        session['pid'] = -1
        session.persist()
        request.response.headerlist.append(('Set-Cookie', session.__dict__['_headers']['cookie_out']))
    return {'experiment': experiment,
            'participant': participant}
