# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
from pyramid.view import view_config

from ess.models import (DBSession, Experiment, Participant)


def init(config):
    config.add_route('experiment.run', '/run/{ueid}')


def remaining_pages(request, qsheet, seen=None):
    if seen is None:
        seen = []
    if qsheet.id in seen:
        return (1, None)
    else:
        pages = (None, 0)
        for successor in qsheet.next:
            if successor.target:
                next_pages = remaining_pages(request, successor.target, seen)
                if pages[0] is None or pages[0] > next_pages[0]:
                    pages = (next_pages[0], pages[1])
                if pages[1] is not None and pages[1] < next_pages[1]:
                    pages = (pages[0], next_pages[1])
        if pages[0] is None:
            pages = (1, pages[1])
        else:
            pages = (pages[0] + 1, pages[1])
        if pages[1] is not None:
            pages = (pages[0], pages[1] + 1)
        return pages


def create_state(request, experiment):
    """Create the initial Participant state for an Experiment."""
    state = {'current': -1,
             'answered': [],
             'pages': remaining_pages(request, experiment.start)}
    return state


def current_participant(request, experiment):
    """Get the current Participant or create a new one."""
    participant = Participant()
    state = create_state(request, experiment)
    participant.set_state(state)
    return participant


@view_config(route_name='experiment.run', renderer='ess:templates/frontend/frontend.kajiki')
def run_survey(request):
    dbsession = DBSession
    experiment = dbsession.query(Experiment).filter(Experiment.external_id == request.matchdict['ueid']).first()
    participant = current_participant(request, experiment)
    qsheet = experiment.qsheets[0]
    qsheet.questions[1]['help'] = 'This works.'
    return {'experiment': experiment,
            'qsheet': qsheet,
            'participant': participant}
