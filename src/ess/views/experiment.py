from pyramid.view import view_config
from pywebtools.pyramid.auth.views import current_user, require_permission


def init(config):
    config.add_route('experiment.create', '/experiments/create')


@view_config(route_name='experiment.create', renderer='ess:templates/experiment/create.kajiki')
@current_user()
@require_permission(permission='experiment.create')
def create(request):
    return {}
