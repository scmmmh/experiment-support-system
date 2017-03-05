# -*- coding: utf-8 -*-
import json
import transaction

from alembic import config, command
from pkg_resources import resource_string
from pyramid.paster import (get_appsettings, setup_logging)
from pywebtools.sqlalchemy import DBSession, Base
from pywebtools.pyramid.auth.models import User, PermissionGroup, Permission
from sqlalchemy import engine_from_config

from ess.views.admin import load_question_types


def init(subparsers):
    parser = subparsers.add_parser('initialise-database', help='Initialise the database')
    parser.add_argument('configuration', help='Experiment Support System configuration file')
    parser.add_argument('--drop-existing', action='store_true', default=False, help='Drop any existing tables')
    parser.set_defaults(func=initialise_database)


def initialise_database(args):
    settings = get_appsettings(args.configuration)
    setup_logging(args.configuration)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    if args.drop_existing:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    dbsession = DBSession()
    with transaction.manager:
        user = User(email='admin@example.com', display_name='Admin', status='active')
        user.new_password('password')
        group = PermissionGroup(title='Site administrator')
        group.permissions.append(Permission(name='admin.users.view', title='View all users'))
        group.permissions.append(Permission(name='admin.users.edit', title='Edit all users'))
        group.permissions.append(Permission(name='admin.users.delete', title='Delete all users'))
        group.permissions.append(Permission(name='admin.users.permissions', title='Edit all user\'s permissions'))
        user.permission_groups.append(group)
        group = PermissionGroup(title='Developer')
        group.permissions.append(Permission(name='experiment.create', title='Create new experiments'))
        user.permission_groups.append(group)
        dbsession.add(user)
        group = PermissionGroup(title='Content administrator')
        group.permissions.append(Permission(name='experiment.view', title='View all experiments'))
        group.permissions.append(Permission(name='experiment.edit', title='Edit all experiments'))
        group.permissions.append(Permission(name='experiment.delete', title='Delete all experiments'))
        dbsession.add(group)
        load_question_types(dbsession,
                            json.loads(resource_string('ess', 'scripts/templates/default_question_types.json').\
                                       decode('utf-8')))
        from ess.models import Experiment, Page, Question, Transition, DataSet, DataItem
        exp = Experiment(title='Test 1', owned_by=1, external_id='1', status='develop')
        dbsession.add(exp)
        page1 = Page(name='test1', title='Page 1', experiment=exp)
        exp.start = page1
        dbsession.add(page1)
        q = Question(page=page1, type_id=1, order=0, attributes={'text': 'Welcome to the experiment.'})
        dbsession.add(q)
        q = Question(page=page1, type_id=3, order=1, attributes={'name': 'q1', 'title': 'Informed Consent', 'allow_multiple': True, 'answers': [{'value': 'yes', 'label': 'I consent to the experiment'}], 'required': True})
        dbsession.add(q)
        page2 = Page(name='test2', title='Page 2', experiment=exp)
        dbsession.add(page2)
        q = Question(page=page2, type_id=1, order=0, attributes={'text': 'This is to determine our user group.'})
        dbsession.add(q)
        q = Question(page=page2, type_id=3, order=1, attributes={'name': 'q1', 'title': 'Gender', 'answers': [{'value': 'female', 'label': 'Female'}, {'value': 'male', 'label': 'Male'}], 'required': True})
        dbsession.add(q)
        q = Question(page=page2, type_id=3, order=2, attributes={'name': 'q2', 'title': 'Education', 'answers': [{'value': 'youtube', 'label': 'YouTube'}, {'value': 'uni', 'label': 'University'}], 'allow_multiple': True, 'required': True})
        dbsession.add(q)
        trans = Transition(source=page1, target=page2, order=0)
        dbsession.add(trans)
        page3 = Page(name='test3', title='Page 3', experiment=exp)
        dbsession.add(page3)
        q = Question(page=page3, type_id=1, order=0, attributes={'text': 'Here are some questions.'})
        dbsession.add(q)
        q = Question(page=page3, type_id=4, order=1, attributes={'name': 'q1', 'title': 'Some Questions', 'questions': [{'name': 's1', 'label': 'Q1'}, {'name': 's2', 'label': 'Q2'}], 'answers': [{'value': 'a', 'label': 'A'}, {'value': 'b', 'label': 'B'}], 'required': True})
        dbsession.add(q)
        q = Question(page=page3, type_id=4, order=2, attributes={'name': 'q2', 'title': 'Some Questions', 'questions': [{'name': 's1', 'label': 'Q1'}, {'name': 's2', 'label': 'Q2'}], 'answers': [{'value': 'a', 'label': 'A'}, {'value': 'b', 'label': 'B'}], 'required': True, 'allow_multiple': True})
        dbsession.add(q)
        trans = Transition(source=page2, target=page3, order=0)
        dbsession.add(trans)
        page4 = Page(name='test4', title='Page 4', experiment=exp)
        dbsession.add(page4)
        q = Question(page=page4, type_id=1, order=0, attributes={'text': 'Here are some questions.'})
        dbsession.add(q)
        q = Question(page=page4, type_id=5, order=1, attributes={'name': 'q1', 'title': 'Some Questions', 'answers': [{'value': 'a', 'label': 'A'}, {'value': 'b', 'label': 'B'}, {'value': 'c', 'label': 'C'}], 'required': True})
        dbsession.add(q)
        trans = Transition(source=page3, target=page4, order=0)
        dbsession.add(trans)
        page5 = Page(name='test5', title='Page 5', experiment=exp)
        dbsession.add(page5)
        q = Question(page=page5, type_id=1, order=0, attributes={'text': 'Here are some questions.'})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=1, attributes={'name': 'q1', 'title': 'Question 1', 'input_type': 'text', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=2, attributes={'name': 'q2', 'title': 'Question 2', 'input_type': 'textarea', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=3, attributes={'name': 'q3', 'title': 'Question 3', 'input_type': 'number', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=4, attributes={'name': 'q4', 'title': 'Question 4', 'input_type': 'email', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=5, attributes={'name': 'q5', 'title': 'Question 5', 'input_type': 'url', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=6, attributes={'name': 'q6', 'title': 'Question 6', 'input_type': 'date', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=7, attributes={'name': 'q7', 'title': 'Question 7', 'input_type': 'time', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=8, attributes={'name': 'q8', 'title': 'Question 8', 'input_type': 'datetime', 'required': True})
        dbsession.add(q)
        q = Question(page=page5, type_id=2, order=8, attributes={'name': 'q9', 'title': 'Question 9', 'input_type': 'month', 'required': True})
        dbsession.add(q)
        trans = Transition(source=page4, target=page5, order=0)
        dbsession.add(trans)
        page6 = Page(name='test6', title='Page 6', experiment=exp)
        dbsession.add(page6)
        q = Question(page=page6, type_id=1, order=0, attributes={'text': 'This page will submit automatically after five seconds.'})
        dbsession.add(q)
        q = Question(page=page6, type_id=7, order=1, attributes={'name': 'q1'})
        dbsession.add(q)
        q = Question(page=page6, type_id=8, order=1, attributes={'name': 'q2', 'delay': 5})
        dbsession.add(q)
        trans = Transition(source=page5, target=page6, order=0)
        dbsession.add(trans)
        page7 = Page(name='test7', title='Page 7', experiment=exp)
        dbsession.add(page7)
        q = Question(page=page7, type_id=1, order=0, attributes={'text': 'This page has language / country questions.'})
        dbsession.add(q)
        q = Question(page=page7, type_id=9, order=1, attributes={'name': 'q1', 'title': 'Select your favourite language', 'required': True})
        dbsession.add(q)
        q = Question(page=page7, type_id=10, order=2, attributes={'name': 'q2', 'title': 'Select your favourite country', 'required': True})
        dbsession.add(q)
        trans = Transition(source=page6, target=page7, order=0)
        dbsession.add(trans)

        exp = Experiment(title='Branching Test 1', owned_by=1, external_id='2', status='develop')
        dbsession.add(exp)
        page1 = Page(name='consent', title='Informed Consent', experiment=exp)
        exp.start = page1
        dbsession.add(page1)
        q = Question(page=page1, type_id=1, order=0, attributes={'text': 'Welcome to the experiment.'})
        dbsession.add(q)
        q = Question(page=page1, type_id=3, order=1, attributes={'name': 'q1', 'title': 'Informed Consent', 'allow_multiple': True, 'answers': [{'value': 'yes', 'label': 'I consent to the experiment'}], 'required': True})
        dbsession.add(q)
        page2 = Page(name='background', title='Background', experiment=exp)
        dbsession.add(page2)
        q = Question(page=page2, type_id=1, order=0, attributes={'text': 'This is to determine our user group.'})
        dbsession.add(q)
        qg = Question(page=page2, type_id=3, order=1, attributes={'name': 'q1', 'title': 'Gender', 'answers': [{'value': 'female', 'label': 'Female'}, {'value': 'male', 'label': 'Male'}], 'required': True})
        dbsession.add(qg)
        trans = Transition(source=page1, target=page2, order=0)
        page3 = Page(name='female', title='Female', experiment=exp)
        dbsession.add(page3)
        q = Question(page=page3, type_id=1, order=0, attributes={'text': 'You selected "female" as your gender.'})
        dbsession.add(q)
        page4 = Page(name='male', title='Male', experiment=exp)
        dbsession.add(page4)
        q = Question(page=page4, type_id=1, order=0, attributes={'text': 'You selected "male" as your gender.'})
        dbsession.add(q)
        dbsession.flush()
        trans = Transition(source=page2, target=page3, order=0)
        trans['condition'] = {'type': 'answer', 'page': page2.id, 'question': qg.id, 'value': 'female'}
        dbsession.add(trans)
        trans = Transition(source=page2, target=page4, order=1)
        trans['condition'] = {'type': 'answer', 'page': page2.id, 'question': qg.id, 'value': 'male'}
        dbsession.add(trans)

        exp = Experiment(title='Sampling Test 1', owned_by=1, external_id='3', status='develop')
        dbsession.add(exp)
        page1 = Page(name='crowd', title='Crowd Sourcing', experiment=exp)
        exp.start = page1
        dbsession.add(page1)
        q = Question(page=page1, type_id=1, order=0, attributes={'text': 'You are voting for: ${name}.'})
        dbsession.add(q)
        q = Question(page=page1, type_id=3, order=1, attributes={'name': 'vote', 'title': 'Vote', 'answers': [{'value': 'up', 'label': 'Yes'}, {'value': 'down', 'label': 'No'}], 'required': True})
        dbsession.add(q)
        ds = DataSet(experiment=exp, name='superheroes', type='dataset')
        ds['columns'] = ['name']
        dbsession.add(ds)
        di = DataItem(data_set=ds, order=0)
        di['values'] = {'name': 'Batman'}
        di = DataItem(data_set=ds, order=1)
        di['values'] = {'name': 'Superman'}
        di = DataItem(data_set=ds, order=2)
        di['values'] = {'name': 'Captain America'}
        di = DataItem(data_set=ds, order=3)
        di['values'] = {'name': 'Wonder Woman'}
        di = DataItem(data_set=ds, order=4)
        di['values'] = {'name': 'The Hulk'}
        di = DataItem(data_set=ds, order=5)
        di['values'] = {'name': 'Iron Man'}
        di = DataItem(data_set=ds, order=6)
        di['values'] = {'name': 'Black Widow'}
        di = DataItem(data_set=ds, order=7)
        di['values'] = {'name': 'Scarlett Witch'}
        di = DataItem(data_set=ds, order=8)
        di['values'] = {'name': 'Mr Incredible'}
        di = DataItem(data_set=ds, order=9)
        di['values'] = {'name': 'Elastigirl'}

        exp = Experiment(title='Latin Square Test 1', owned_by=1, external_id='4', status='develop')
        dbsession.add(exp)
        page1 = Page(name='page1', title='Page 1', experiment=exp)
        exp.start = page1
        dbsession.add(page1)
        q = Question(page=page1, type_id=1, order=0, attributes={'text': 'You are undertaking ${title} with ${label}.'})
        dbsession.add(q)
        q = Question(page=page1, type_id=7, order=1, attributes={'name': 'q1'})
        dbsession.add(q)
        page2 = Page(name='page2', title='Page 2', experiment=exp)
        dbsession.add(page1)
        q = Question(page=page2, type_id=1, order=0, attributes={'text': 'How did you feel about that?'})
        dbsession.add(q)
        q = Question(page=page2, type_id=3, order=1, attributes={'name': 'vote', 'title': 'Vote', 'answers': [{'value': 'up', 'label': 'Yes'}, {'value': 'down', 'label': 'No'}], 'required': True})
        dbsession.add(q)
        ds = DataSet(experiment=exp, name='tasks', type='dataset')
        ds['columns'] = ['task', 'title']
        dbsession.add(ds)
        di = DataItem(data_set=ds, order=0)
        di['values'] = {'task': 'task1', 'title': 'Task 1'}
        di = DataItem(data_set=ds, order=1)
        di['values'] = {'task': 'task2', 'title': 'Task 2'}
        di = DataItem(data_set=ds, order=2)
        di['values'] = {'task': 'task3', 'title': 'Task 3'}
        ds = DataSet(experiment=exp, name='interfaces', type='dataset')
        ds['columns'] = ['interface', 'label']
        dbsession.add(ds)
        di = DataItem(data_set=ds, order=0)
        di['values'] = {'interface': 'interface1', 'label': 'Interface 1'}
        di = DataItem(data_set=ds, order=1)
        di['values'] = {'interface': 'interface2', 'label': 'Interface 2'}

    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'ess:migrations')
    command.stamp(alembic_config, "head")
