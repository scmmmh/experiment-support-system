from pyramid.view import view_config
from pywebtools.pyramid.auth.views import current_user

from . import frontend, user, experiment


def init(config):
    config.add_route('root', '/')
    config.add_route('dashboard', '/dashboard')
    user.init(config)
    frontend.init(config)
    experiment.init(config)


@view_config(route_name='root', renderer='ess:templates/root.kajiki')
@current_user()
def root(request):
    return {}


@view_config(route_name='dashboard', renderer='ess:templates/dashboard.kajiki')
@current_user()
def dashboard(request):
    return {}
