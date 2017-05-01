# -*- coding: utf-8 -*-
"""
#################################################################
:mod:`ess_test.views_test.root_test` - Root View Functional Tests
#################################################################

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)


def test_root_no_public_experiments(functional_tester):
    """Tests the root view with no publicly listed experiments.
    """
    functional_tester.get_url('/')
    functional_tester.has_text('Experiment Support System')
    functional_tester.has_text('There are currently no experiments available for participation')
    functional_tester.create_model('Experiment', {'title': 'This is a test experiment',
                                                  'status': 'running',
                                                  'public': False,
                                                  'owned_by': functional_tester.get_model('User',
                                                                                          "username == 'admin'").id})
    functional_tester.get_url('/')
    functional_tester.has_text('Experiment Support System')
    functional_tester.has_text('There are currently no experiments available for participation')


def test_root_public_experiments(functional_tester):
    """Tests the root view with a publicly listed experiment.
    """
    functional_tester.create_model('Experiment', {'title': 'This is a test experiment',
                                                  'status': 'running',
                                                  'public': True,
                                                  'owned_by': functional_tester.get_model('User',
                                                                                          "username == 'admin'").id})
    functional_tester.get_url('/')
    functional_tester.has_text('Experiment Support System')
    functional_tester.has_text('The following experiments are currently available for participation')
    functional_tester.has_text('This is a test experiment')
