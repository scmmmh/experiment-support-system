import formencode
import transaction
import uuid

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.sqlalchemy import DBSession

from ess.models import Experiment
from ess.validators import PageExistsValidator


def init(config):
    config.add_route('experiment.create', '/experiments/create')
    config.add_route('experiment.view', '/experiments/{eid}')
    config.add_route('experiment.settings.general', '/experiments/{eid}/settings/general')
    config.add_route('experiment.settings.display', '/experiments/{eid}/settings/display')


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
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)}]}
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
                params = SettingsGeneralSchema().to_python(request.params, State(request=request))
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
