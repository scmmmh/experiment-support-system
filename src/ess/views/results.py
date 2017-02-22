import formencode
import transaction

from collections import Counter
from datetime import datetime, timedelta
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.pyramid.decorators import require_method
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import and_, func

from ess.models import Experiment, Participant, Question, Answer, Page
from ess.validators import PageNameUniqueValidator, QuestionEditSchema, PageExistsValidator, QuestionExistsValidator, DataSetExistsValidator


def init(config):
    config.add_route('experiment.results', '/experiments/{eid}/results')
    config.add_route('experiment.results.export', '/experiments/{eid}/results/export')


@view_config(route_name='experiment.results', renderer='ess:templates/results/overview.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def overview(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        time_boundary = datetime.now() - timedelta(minutes=20)
        overall = {'total': dbsession.query(func.count(Participant.id.unique)).filter(Participant.experiment_id == experiment.id).first()[0],
                   'completed': dbsession.query(func.count(Participant.id.unique)).filter(and_(Participant.experiment_id == experiment.id,
                                                                                               Participant.completed == True)).first()[0],
                   'in_progress': dbsession.query(func.count(Participant.id.unique)).filter(and_(Participant.experiment_id == experiment.id,
                                                                                                 Participant.completed == False,
                                                                                                 Participant.updated >= time_boundary)).first()[0],
                   'abandoned': dbsession.query(func.count(Participant.id.unique)).filter(and_(Participant.experiment_id == experiment.id,
                                                                                               Participant.completed == False,
                                                                                               Participant.updated < time_boundary)).first()[0]}
        
        in_progress = {}
        abandoned = {}
        for participant in dbsession.query(Participant).filter(and_(Participant.experiment_id == experiment.id,
                                                                    Participant.completed == False)):
            if participant.updated >= time_boundary:
                if participant['current'] in in_progress:
                    in_progress[participant['current']] = in_progress[participant['current']] + 1
                else:
                    in_progress[participant['current']] = 1
            else:
                if participant['current'] in abandoned:
                    abandoned[participant['current']] = abandoned[participant['current']] + 1
                else:
                    abandoned[participant['current']] = 1
        summary = {}
        for answer in dbsession.query(Answer).join(Participant).join(Question).join(Page).filter(and_(Participant.experiment_id == experiment.id,
                                                                                                      Participant.completed == True)):
            if answer.question.page.id not in summary:
                summary[answer.question.page.id] = {'questions': {}}
            if answer.question['frontend', 'display_as'] == 'simple_input':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = Counter()
                if answer['response']:
                    summary[answer.question.page.id]['questions'][answer.question.id].update([answer['response']])
            elif answer.question['frontend', 'display_as'] == 'select_simple_choice':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = Counter()
                if isinstance(answer['response'], list):
                    summary[answer.question.page.id]['questions'][answer.question.id].update(answer['response'])
                else:
                    summary[answer.question.page.id]['questions'][answer.question.id].update([answer['response']])
            elif answer.question['frontend', 'display_as'] == 'select_grid_choice':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = {}
                for key, value in answer['response'].items():
                    if key not in summary[answer.question.page.id]['questions'][answer.question.id]:
                        summary[answer.question.page.id]['questions'][answer.question.id][key] = Counter()
                    if isinstance(value, list):
                        summary[answer.question.page.id]['questions'][answer.question.id][key].update(value)
                    else:
                        summary[answer.question.page.id]['questions'][answer.question.id][key].update([value])
            elif answer.question['frontend', 'display_as'] == 'ranking':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = Counter()
                summary[answer.question.page.id]['questions'][answer.question.id].update([' - '.join(answer['response'])])
            if answer.question.page.dataset_id is not None:
                if 'dataset' not in summary[answer.question.page.id]:
                    summary[answer.question.page.id]['dataset'] = Counter()
                summary[answer.question.page.id]['dataset'].update([answer.data_item_id])
        return {'experiment': experiment,
                'overall': overall,
                'in_progress': in_progress,
                'abandoned': abandoned,
                'summary': summary,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Results',
                            'url': request.route_url('experiment.results', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()
