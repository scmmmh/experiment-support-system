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
from sqlalchemy import and_

from ess.models import (DBSession, Experiment, Page, Participant, Question, Answer)
from ess.validators import FrontendPageSchema


def init(config):
    config.add_route('experiment.run', '/run/{ueid}')
    config.add_route('experiment.completed', '/run/{ueid}/complete')


def remaining_pages(page, seen=None):
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


def next_page(dbsession, participant, page):
    if page.next:
        for transition in page.next:
            if 'condition' in transition:
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
            else:
                return transition.target.id
    return None


def flatten_errors(errors):
    result = []
    for k, v in errors.items():
        if isinstance(v, dict):
            tmp = flatten_errors(v)
            for (sub_k, sub_v) in tmp.items():
                result.append(('%s.%s' % (k, sub_k), sub_v))
        else:
            result.append((k, v))
    return dict(result)


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
        participant['progress'] = determine_progress(participant, page)
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
                params = FrontendPageSchema(page.questions, [None]).to_python(request.params, State(request=request))
                for question in page.questions:
                    if question['frontend', 'display_as'] != 'text':
                        answer = Answer(participant_id=participant.id,
                                        question_id=question.id,
                                        data_item_id=None)
                        answer['response'] = params[question['name']]
                        if isinstance(answer['response'], list) and len(question['frontend', 'answers']) == 1:
                            answer['response'] = answer['response'][0]
                        dbsession.add(answer)
                participant['answered'].append(page.id)
                participant['current'] = next_page(dbsession, participant, page)
            dbsession.add(experiment)
            raise HTTPFound(request.route_url('experiment.run', ueid=experiment.external_id))
        except formencode.Invalid as e:
            print(flatten_errors(e.unpack_errors()))
            dbsession.add(experiment)
            dbsession.add(page)
            dbsession.add(participant)
            return {'experiment': experiment,
                    'page': page,
                    'participant': participant,
                    'values': request.params,
                    'errors': flatten_errors(e.unpack_errors())}
    dbsession.add(experiment)
    dbsession.add(page)
    dbsession.add(participant)
    return {'experiment': experiment,
            'page': page,
            'participant': participant}


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
