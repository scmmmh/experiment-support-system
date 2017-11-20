# -*- coding: utf-8 -*-
"""
#########################################################################
:mod:`ess_test.views_test.frontend_test` - Frontend View Functional Tests
#########################################################################

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""


def test_no_start_experiment(pyramid_app_tester, database_tester):
    """Test that non-existing experiment return 404."""
    app, db = pyramid_app_tester, database_tester
    app.goto('/run/this_is_missing')
    app.has_status(404)


def test_single_page_just_page_experiment(pyramid_app_tester, database_tester):
    """Test a single page experiment."""
    app, db = pyramid_app_tester, database_tester
    exp = db.create_model('Experiment', {'title': 'This is a test experiment',
                                         'status': 'live',
                                         'public': False,
                                         'external_id': 'external_id',
                                         'owner': db.get_model('User', ('email', '==', 'admin@example.com'))})
    page = db.create_model('Page', {'title': 'Page 1',
                                    'name': 'page1',
                                    'experiment': exp})
    db.update(exp, start=page)
    app.goto('/run/%s' % exp.external_id)
    app.has_text('This is a test experiment')
    app.has_text('Page 1')


def test_single_page_just_text_experiment(pyramid_app_tester, database_tester):
    """Test a single page experiment with just a single text question."""
    app, db = pyramid_app_tester, database_tester
    exp = db.create_model('Experiment', {'title': 'This is a test experiment',
                                         'status': 'live',
                                         'public': False,
                                         'external_id': 'external_id',
                                         'owner': db.get_model('User', ('email', '==', 'admin@example.com'))})
    page = db.create_model('Page', {'title': 'Page 1',
                                    'name': 'page1',
                                    'experiment': exp})
    db.update(exp, start=page)
    db.create_model('Question', {'page': page,
                                 'q_type': db.get_model('QuestionType', ('name', '==', 'text')),
                                 'order': 1,
                                 'attributes': {'text': 'This is some text to show'}})
    app.goto('/run/%s' % exp.external_id)
    app.has_text('This is a test experiment')
    app.has_text('Page 1')
    app.has_text('This is some text to show')


def test_no_data_submission(pyramid_app_tester, database_tester):
    """Test submitting a page with no questions."""
    app, db = pyramid_app_tester, database_tester
    exp = db.create_model('Experiment', {'title': 'This is a test experiment',
                                         'status': 'live',
                                         'public': False,
                                         'external_id': 'external_id',
                                         'owner': db.get_model('User', ('email', '==', 'admin@example.com'))})
    page = db.create_model('Page', {'title': 'Page 1',
                                    'name': 'page1',
                                    'experiment': exp})
    db.update(exp, start=page)
    app.goto('/run/%s' % exp.external_id)
    app.has_text('This is a test experiment')
    app.has_text('Page 1')
    app.submit_form(form_idx=0, values={'_action': 'next-page'})
    app.follow_redirect()
    app.follow_redirect()
    app.has_text('This is a test experiment - Completed')


def test_single_page_just_simple_question_submission_experiment(pyramid_app_tester, database_tester):
    app, db = pyramid_app_tester, database_tester
    exp = db.create_model('Experiment', {'title': 'This is a test experiment',
                                         'status': 'live',
                                         'public': False,
                                         'external_id': 'external_id',
                                         'owner': db.get_model('User', ('email', '==', 'admin@example.com'))})
    page = db.create_model('Page', {'title': 'Page 1',
                                    'name': 'page1',
                                    'experiment': exp})
    db.update(exp, start=page)
    question_id = db.create_model('Question', {'page': page,
                                               'q_type': db.get_model('QuestionType', ('name', '==', 'simple_input')),
                                               'order': 1,
                                               'attributes': {'name': 'question_1',
                                                              'title': 'Question 1'}}).id
    app.goto('/run/%s' % exp.external_id)
    app.has_text('This is a test experiment')
    app.has_text('Page 1')
    app.has_text('Question 1')
    app.submit_form(form_idx=0, values={'_action': 'next-page',
                                        'question_1': 'Testing'})
    db.flush()
    app.follow_redirect()
    #answer = db.get_model('Answer', ('question_id', '==', question_id))
    app.follow_redirect()
    app.has_text('This is a test experiment - Completed')
