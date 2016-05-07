# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
from pyramid.view import view_config

from ess.models import (DBSession, Experiment)

def init(config):
    config.add_route('experiment.run', '/run/{ueid}')


@view_config(route_name='experiment.run', renderer='ess:templates/frontend/frontend.kajiki')
def run_survey(request):
    dbsession = DBSession
    experiment = dbsession.query(Experiment).filter(Experiment.external_id == request.matchdict['ueid']).first()
    return {'experiment': experiment}
