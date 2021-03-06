import formencode
import transaction
import uuid

from copy import deepcopy
from datetime import datetime, timedelta
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.sqlalchemy import DBSession
from pywebtools.pyramid.util import paginate
from sqlalchemy import func, and_

from ess.importexport import ExperimentIOSchema, replace_questions, fix_latin_square, fix_transition, all_io_schemas
from ess.models import (Experiment, Participant)
from ess.validators import PageExistsValidator


def init(config):
    config.add_route('experiment.list', '/experiments')
    config.add_route('experiment.create', '/experiments/create')
    config.add_route('experiment.import', '/experiments/import')
    config.add_route('experiment.view', '/experiments/{eid}')
    config.add_route('experiment.settings.general', '/experiments/{eid}/settings/general')
    config.add_route('experiment.settings.display', '/experiments/{eid}/settings/display')
    config.add_route('experiment.actions', '/experiments/{eid}/actions')
    config.add_route('experiment.actions.export', '/experiments/{eid}/actions/export')
    config.add_route('experiment.actions.duplicate', '/experiments/{eid}/actions/duplicate')
    config.add_route('experiment.actions.delete', '/experiments/{eid}/actions/delete')
    config.add_route('experiment.status', '/experiments/{eid}/status')


@view_config(route_name='experiment.list', renderer='ess:templates/experiment/list.kajiki')
@current_user()
@require_permission(permission='experiment.view')
def list_experiments(request):
    dbsession = DBSession()
    experiments = dbsession.query(Experiment)
    query_params = []
    if 'q' in request.params and request.params['q'].strip():
        experiments = experiments.filter(Experiment.title.like('%%%s%%' % request.params['q'].strip()))
        query_params.append(('q', request.params['q'].strip()))
    start = 0
    if 'start' in request.params:
        try:
            start = int(request.params['start'])
        except ValueError:
            pass
    experiments = experiments.offset(start).limit(10)
    pages = paginate(request, 'experiment.list', experiments, start, 10, query_params=query_params)
    return {'experiments': experiments,
            'pages': pages}


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
            return {'crumbs': [{'title': 'Experiments',
                                'url': request.route_url('dashboard')},
                               {'title': 'Create',
                                'url': request.route_url('experiment.create')}],
                    'errors': e.error_dict,
                    'values': request.params}
    return {'crumbs': [{'title': 'Experiments',
                        'url': request.route_url('dashboard')},
                       {'title': 'Create',
                        'url': request.route_url('experiment.create')}]}


class ImportExperimentSchema(CSRFSchema):

    source = formencode.validators.FieldStorageUploadConverter(not_empty=True)


@view_config(route_name='experiment.import', renderer='ess:templates/experiment/import.kajiki')
@current_user()
@require_permission(permission='experiment.create')
def import_experiment(request):
    if request.method == 'POST':
        try:
            params = ImportExperimentSchema().to_python(request.params, State(request=request))
            dbsession = DBSession()
            with transaction.manager:
                experiment, errors = ExperimentIOSchema(include_schemas=[s for s in all_io_schemas
                                                                         if s != ExperimentIOSchema]).\
                    loads(params['source'].file.read().decode('utf-8'))
                if errors:
                    raise formencode.Invalid('. '.join(['%s: %s' % (e['source']['pointer'], e['detail'])
                                                        for e in errors['errors']]), None, None)
                for page in experiment.pages:
                    replace_questions(page, dbsession)
                experiment.owner = request.current_user
                experiment.external_id = uuid.uuid1().hex,
                experiment.status = 'develop'
                dbsession.add(experiment)
                dbsession.flush()
                for latin_square in experiment.latin_squares:
                    fix_latinsquare(latin_square, experiment.data_sets)
                for page in experiment.pages:
                    for transition in page.next:
                        fix_transition(transition, experiment.pages)
            dbsession.add(experiment)
            raise HTTPFound(request.route_url('experiment.view', eid=experiment.id))
        except formencode.Invalid as e:
            return {'crumbs': [{'title': 'Experiments',
                                'url': request.route_url('dashboard')},
                               {'title': 'Import',
                                'url': request.route_url('experiment.import')}],
                    'errors': {'source': str(e)},
                    'values': request.params}
    return {'crumbs': [{'title': 'Experiments',
                        'url': request.route_url('dashboard')},
                       {'title': 'Import',
                        'url': request.route_url('experiment.import')}]}


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
            overall = {'total': dbsession.query(func.count(Participant.id.unique)).
                       filter(Participant.experiment_id == experiment.id).first()[0],
                       'completed': dbsession.query(func.count(Participant.id.unique)).
                       filter(and_(Participant.experiment_id == experiment.id,
                                   Participant.completed == True)).first()[0],  # noqa: E712
                       'in_progress': dbsession.query(func.count(Participant.id.unique)).
                       filter(and_(Participant.experiment_id == experiment.id,
                                   Participant.completed == False,
                                   Participant.updated >= time_boundary)).first()[0],
                       'abandoned': dbsession.query(func.count(Participant.id.unique)).
                       filter(and_(Participant.experiment_id == experiment.id,
                                   Participant.completed == False,
                                   Participant.updated < time_boundary)).first()[0]}
            result['overall'] = overall
            result['in_progress'] = {}
            result['abandoned'] = {}
            for participant in dbsession.query(Participant).filter(and_(Participant.experiment_id == experiment.id,
                                                                        Participant.completed == False)):  # noqa: E712
                if participant.updated >= time_boundary:
                    if participant['current'] in result['in_progress']:
                        result['in_progress'][participant['current']] = \
                            result['in_progress'][participant['current']] + 1
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


@view_config(route_name='experiment.actions', renderer='ess:templates/experiment/actions/index.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def actions(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Actions',
                            'url': request.route_url('experiment.actions', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DeleteSchema(CSRFSchema):

    confirm = formencode.validators.OneOf(['true'],
                                          messages={'notIn': 'Please confirm that you wish to delete this experiment.',
                                                    'missing': 'Please confirm that you wish to delete this experiment.'})  # noqa: E501


@view_config(route_name='experiment.actions.delete', renderer='ess:templates/experiment/actions/delete.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='delete')
def actions_delete(request):
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
                                   {'title': 'Actions',
                                    'url': request.route_url('experiment.actions', eid=experiment.id)},
                                   {'title': 'Delete',
                                    'url': request.route_url('experiment.actions.delete', eid=experiment.id)}],
                        'errors': e.error_dict,
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Actions',
                            'url': request.route_url('experiment.actions', eid=experiment.id)},
                           {'title': 'Delete',
                            'url': request.route_url('experiment.actions.delete', eid=experiment.id)}]}
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
                        for participant in dbsession.query(Participant).\
                                filter(Participant.experiment_id == experiment.id):
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


@view_config(route_name='experiment.actions.export', renderer='ess:templates/experiment/actions/export.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def actions_export(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                CSRFSchema().to_python(request.params, State(request=request))
                request.response.headers['Content-Disposition'] = 'attachment; filename="%s.json"' % experiment.title
                request.override_renderer = 'json'
                return ExperimentIOSchema(include_schemas=[s for s in all_io_schemas if s != ExperimentIOSchema]).\
                    dump(experiment).data
            except formencode.Invalid:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Actions',
                                    'url': request.route_url('experiment.actions', eid=experiment.id)},
                                   {'title': 'Export',
                                    'url': request.route_url('experiment.actions.export', eid=experiment.id)}]}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Actions',
                            'url': request.route_url('experiment.actions', eid=experiment.id)},
                           {'title': 'Export',
                            'url': request.route_url('experiment.actions.export', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DuplicateSchema(CSRFSchema):

    title = formencode.validators.UnicodeString(not_empty=True)


@view_config(route_name='experiment.actions.duplicate', renderer='ess:templates/experiment/actions/duplicate.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def actions_duplicate(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = DuplicateSchema().to_python(request.params, State(request=request))
                data = ExperimentIOSchema(include_schemas=[s for s in all_io_schemas if s != ExperimentIOSchema]).\
                    dump(experiment).data
                data = deepcopy(data)
                with transaction.manager:
                    dbsession.add(experiment)
                    new_experiment, errors = ExperimentIOSchema(include_schemas=[s for s in all_io_schemas
                                                                                 if s != ExperimentIOSchema]).\
                        load(data)
                    if errors:
                        raise formencode.Invalid('. '.join(['%s: %s' % (e['source']['pointer'], e['detail'])
                                                            for e in errors['errors']]), None, None)
                    for page in new_experiment.pages:
                        replace_questions(page, dbsession)
                    new_experiment.title = params['title']
                    new_experiment.owner = request.current_user
                    new_experiment.external_id = uuid.uuid1().hex,
                    new_experiment.status = 'develop'
                    dbsession.add(new_experiment)
                    dbsession.flush()
                    for latin_square in new_experiment.latin_squares:
                        fix_latin_square(latin_square, new_experiment.data_sets)
                    for page in new_experiment.pages:
                        for transition in page.next:
                            fix_transition(transition, new_experiment.pages)
                dbsession.add(new_experiment)
                raise HTTPFound(request.route_url('experiment.view', eid=new_experiment.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Actions',
                                    'url': request.route_url('experiment.actions', eid=experiment.id)},
                                   {'title': 'Duplicate',
                                    'url': request.route_url('experiment.actions.duplicate', eid=experiment.id)}],
                        'errors': e.error_dict if e.error_dict else {'title': str(e)},
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Actions',
                            'url': request.route_url('experiment.actions', eid=experiment.id)},
                           {'title': 'Duplicate',
                            'url': request.route_url('experiment.actions.duplicate', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()
