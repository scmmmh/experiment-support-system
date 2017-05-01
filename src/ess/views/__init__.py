from pyramid.view import view_config
from pywebtools.pyramid.auth.views import current_user
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import and_

from . import frontend, user, experiment, page, data, results
from ess.models import Experiment


def init(config):
    config.add_route('root', '/')
    config.add_route('dashboard', '/dashboard')
    user.init(config)
    frontend.init(config)
    experiment.init(config)
    page.init(config)
    data.init(config)
    results.init(config)


@view_config(route_name='root', renderer='ess:templates/root.kajiki')
@current_user()
def root(request):
    dbsession = DBSession()
    experiments = dbsession.query(Experiment).filter(and_(Experiment.status == 'live',
                                                          Experiment.public == True)).order_by(Experiment.title)  # noqa: E712,E501
    return {'experiments': experiments}


@view_config(route_name='dashboard', renderer='ess:templates/dashboard.kajiki')
@current_user()
def dashboard(request):
    dbsession = DBSession()
    experiments = dbsession.query(Experiment).filter(Experiment.owned_by == request.current_user.id).\
        order_by(Experiment.title)
    return {'experiments': experiments,
            'crumbs': [{'title': 'Experiments',
                        'url': request.route_url('dashboard')}]}
