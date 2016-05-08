# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
from pyramid.view import view_config

from ess.models import (DBSession, Experiment, QSheet, Question, QuestionType, QuestionTypeGroup)

def init(config):
    config.add_route('experiment.run', '/run/{ueid}')


@view_config(route_name='experiment.run', renderer='ess:templates/frontend/frontend.kajiki')
def run_survey(request):
    dbsession = DBSession
    experiment = Experiment(title='Test Experiment')
    qsheet = QSheet(title='Test Page', name='p1')
    question = Question(title='Question 1', name='q1')
    question.attributes = {'width': '6',
                           'input-type': 'date',
                           'help': 'Just give us a date'}
    question.q_type = QuestionType(name='text', q_type_group=QuestionTypeGroup(name='default'))
    question.q_type.display_as = 'single_line'
    question.q_type.attributes = {'input-type': 'text',
                                  'width': '6'}
    qsheet.questions.append(question)
    return {'experiment': experiment,
            'qsheet': qsheet}
