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
        user = User(email='admin@example.com', display_name='Admin')
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
        from ess.models import Experiment, Page, Question
        exp = Experiment(title='Test', owned_by=1, external_id='1')
        dbsession.add(exp)
        page = Page(name='test1', title='Test 1', experiment=exp)
        exp.start = page
        dbsession.add(page)
        q = Question(page=page, type_id=1, order=0)
        dbsession.add(q)
        q = Question(page=page, type_id=2, order=1, attributes={'name': 'q1', 'title': 'Question 1'})
        dbsession.add(q)
        q = Question(page=page, type_id=3, order=2, attributes={'name': 'q2', 'title': 'Question 2'})
        dbsession.add(q)
        q = Question(page=page, type_id=4, order=3, attributes={'name': 'q3', 'title': 'Question 3'})
        dbsession.add(q)
        q = Question(page=page, type_id=5, order=4, attributes={'name': 'q4', 'title': 'Question 4', 'answers': [{'value': 'dog', 'label': 'Dog'}, {'value': 'cat', 'label': 'Cat'}]})
        dbsession.add(q)
        q = Question(page=page, type_id=6, order=5, attributes={'name': 'q5'})
        dbsession.add(q)
        q = Question(page=page, type_id=7, order=6, attributes={'name': 'q6'})
        dbsession.add(q)
        q = Question(page=page, type_id=8, order=6, attributes={'name': 'q7', 'delay': 200})
        dbsession.add(q)
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'ess:migrations')
    command.stamp(alembic_config, "head")
