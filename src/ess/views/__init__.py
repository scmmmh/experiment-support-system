from pyramid.view import view_config
from pywebtools.pyramid.auth.views import current_user

from . import frontend, user


def init(config):
    config.add_route('root', '/')
    user.init(config)
    frontend.init(config)


@view_config(route_name='root', renderer='ess:templates/root.kajiki')
@current_user()
def root(request):
    return {}
