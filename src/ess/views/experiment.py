from pyramid.view import view_config
from pywebtools.pyramid.auth.views import current_user


def init(config):
    config.add_route('experiment.create', '/experiments/create')
