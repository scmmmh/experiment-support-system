import formencode
import transaction
import uuid

from datetime import datetime, timedelta
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.pyramid.decorators import require_method
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import func, and_

from ess.importexport import export_jsonapi
from ess.models import (Experiment, Participant, Page, Question, QuestionType, QuestionTypeGroup, Transition,
                        DataSet)
from ess.validators import PageExistsValidator


def init(config):
    config.add_route('experiment.create', '/experiments/create')
    config.add_route('experiment.view', '/experiments/{eid}')
    config.add_route('experiment.settings.general', '/experiments/{eid}/settings/general')
    config.add_route('experiment.settings.display', '/experiments/{eid}/settings/display')
    config.add_route('experiment.settings.delete', '/experiments/{eid}/settings/delete')
    config.add_route('experiment.status', '/experiments/{eid}/status')
    config.add_route('experiment.export', '/experiments/{eid}/export')


class CreateExperimentSchema(CSRFSchema):

    title = formencode.validators.UnicodeString(not_empty=True,
                                                messages={'empty': 'Please provide a title'})


@view_config(route_name='experiment.create', renderer='ess:templates/experiment/create.kajiki')
@current_user()
@require_permission(permission='experiment.create')
def create(request):
    if request.method == 'POST':
        try:
            params = CreateExperimentSchema().to_python(request.params, State(request=request))
            dbsession = DBSession()
            with transaction.manager:
                experiment = Experiment(title=params['title'],
                                        summary='',
                                        styles='',
                                        scripts='',
                                        status='develop',
                                        language='en',
                                        external_id=uuid.uuid1().hex,
                                        owned_by=request.current_user.id,
                                        public=False)
                dbsession.add(experiment)
            dbsession.add(experiment)
            raise HTTPFound(request.route_url('experiment.view', eid=experiment.id))
        except formencode.Invalid as e:
            return {'crumbs': [{'title': 'Create Experiment',
                                'url': request.route_url('experiment.create')}],
                    'errors': e.error_dict,
                    'values': request.params}
    return {'crumbs': [{'title': 'Create Experiment',
                        'url': request.route_url('experiment.create')}]}


@view_config(route_name='experiment.view', renderer='ess:templates/experiment/view.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def view(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        result = {'experiment': experiment,
                  'crumbs': [{'title': 'Experiments',
                              'url': request.route_url('dashboard')},
                             {'title': experiment.title,
                              'url': request.route_url('experiment.view', eid=experiment.id)}]}
        if experiment.status in ['live', 'paused', 'completed']:
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
            result['overall'] = overall
            result['in_progress'] = {}
            result['abandoned'] = {}
            for participant in dbsession.query(Participant).filter(and_(Participant.experiment_id == experiment.id,
                                                                        Participant.completed == False)):
                if participant.updated >= time_boundary:
                    if participant['current'] in result['in_progress']:
                        result['in_progress'][participant['current']] = result['in_progress'][participant['current']] + 1
                    else:
                        result['in_progress'][participant['current']] = 1
                else:
                    if participant['current'] in result['abandoned']:
                        result['abandoned'][participant['current']] = result['abandoned'][participant['current']] + 1
                    else:
                        result['abandoned'][participant['current']] = 1
        return result
    else:
        raise HTTPNotFound()


class SettingsGeneralSchema(CSRFSchema):

    title = formencode.validators.UnicodeString(not_empty=True,
                                                messages={'empty': 'Please provide a title'})
    summary = formencode.validators.UnicodeString()
    start = PageExistsValidator()
    language = formencode.validators.OneOf(['en'])
    public = formencode.validators.StringBool(if_missing=False, if_empty=False)


@view_config(route_name='experiment.settings.general', renderer='ess:templates/experiment/settings/general.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def settings_general(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = SettingsGeneralSchema().to_python(request.params, State(request=request,
                                                                                 dbsession=dbsession,
                                                                                 experiment=experiment))
                with transaction.manager:
                    experiment.title = params['title']
                    experiment.summary = params['summary']
                    experiment.start_id = params['start']
                    experiment.language = params['language']
                    experiment.public = params['public']
                    dbsession.add(experiment)
                dbsession.add(experiment)
                raise HTTPFound(request.route_url('experiment.settings.general', eid=experiment.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'General Settings',
                                    'url': request.route_url('experiment.settings.general', eid=experiment.id)}],
                        'errors': e.error_dict,
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'General Settings',
                            'url': request.route_url('experiment.settings.general', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class SettingsDisplaySchema(CSRFSchema):

    styles = formencode.validators.UnicodeString()
    scripts = formencode.validators.UnicodeString()


@view_config(route_name='experiment.settings.display', renderer='ess:templates/experiment/settings/display.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def settings_display(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = SettingsDisplaySchema().to_python(request.params, State(request=request))
                with transaction.manager:
                    experiment.styles = params['styles']
                    experiment.scripts = params['scripts']
                    dbsession.add(experiment)
                dbsession.add(experiment)
                raise HTTPFound(request.route_url('experiment.settings.display', eid=experiment.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Display Settings',
                                    'url': request.route_url('experiment.settings.display', eid=experiment.id)}],
                        'errors': e.error_dict,
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Display Settings',
                            'url': request.route_url('experiment.settings.display', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DeleteSchema(CSRFSchema):

    confirm = formencode.validators.OneOf(['true'],
                                          messages={'notIn': 'Please confirm that you wish to delete this experiment.',
                                                    'missing': 'Please confirm that you wish to delete this experiment.'})


@view_config(route_name='experiment.settings.delete', renderer='ess:templates/experiment/settings/delete.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='delete')
def settings_delete(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                DeleteSchema().to_python(request.params, State(request=request))
                with transaction.manager:
                    dbsession.delete(experiment)
                raise HTTPFound(request.route_url('dashboard'))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Display Settings',
                                    'url': request.route_url('experiment.settings.display', eid=experiment.id)}],
                        'errors': e.error_dict,
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Display Settings',
                            'url': request.route_url('experiment.settings.display', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class StatusSchema(CSRFSchema):

    status = formencode.validators.OneOf(['develop', 'live', 'paused', 'completed'])


@view_config(route_name='experiment.status', renderer='ess:templates/experiment/status.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def status(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = StatusSchema().to_python(request.params, State(request=request))
                with transaction.manager:
                    dbsession.add(experiment)
                    if experiment.status == 'develop' and params['status'] == 'live':
                        for participant in dbsession.query(Participant).filter(Participant.experiment_id == experiment.id):
                            dbsession.delete(participant)
                    experiment.status = params['status']
                dbsession.add(experiment)
                if experiment.status == 'completed':
                    raise HTTPFound(request.route_url('experiment.results', eid=experiment.id))
                else:
                    raise HTTPFound(request.route_url('experiment.view', eid=experiment.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Status',
                                    'url': request.route_url('experiment.status', eid=experiment.id)}],
                        'errors': e.error_dict,
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Status',
                            'url': request.route_url('experiment.status', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.export', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
@require_method('POST')
def export(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        try:
            CSRFSchema().to_python(request.params, State(request=request))
            request.response.headers['Content-Disposition'] = 'attachment; filename=%s.json' % experiment.title
            return export_jsonapi(experiment, includes=[(Experiment, 'pages'), (Experiment, 'start'),
                                                        (Experiment, 'data_sets'), (Experiment, 'latin_squares'),
                                                        (Experiment, 'pages'), (DataSet, 'items'), (Page, 'next'),
                                                        (Page, 'prev'), (Page, 'questions'), (Question, 'q_type'),
                                                        (QuestionType, 'q_type_group'), (QuestionType, 'parent'),
                                                        (QuestionTypeGroup, 'parent')])
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.view', eid=experiment.id))
    else:
        raise HTTPNotFound()
