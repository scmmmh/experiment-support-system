# -*- coding: utf-8 -*-
"""
#################################################################
:mod:`ess_test.views_test.root_test` - Root View Functional Tests
#################################################################

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)


def test_root_no_public_experiments(pyramid_app_tester, database_tester):
    """Tests the root view with no publicly listed experiments.
    """
    app, db = pyramid_app_tester, database_tester
    app.goto('/')
    app.has_text('Experiment Support System')
    app.not_has_text('There are currently no experiments available for participation')
    db.create_model('Experiment', {'title': 'This is a test experiment',
                                   'status': 'live',
                                   'public': False,
                                   'owned_by':db.get_model('User', ('email', '==', 'admin@example.com')).id})
    app.goto('/')
    app.has_text('Experiment Support System')
    app.not_has_text('There are currently no experiments available for participation')


def test_root_public_experiments(pyramid_app_tester, database_tester):
    """Tests the root view with a publicly listed experiment.
    """
    app, db = pyramid_app_tester, database_tester
    db.create_model('Experiment', {'title': 'This is a test experiment',
                                   'status': 'live',
                                   'public': True,
                                    'owned_by': db.get_model('User', ('email', '==', 'admin@example.com')).id})
    app.goto('/')
    app.has_text('Experiment Support System')
    app.has_text('This is a test experiment')
