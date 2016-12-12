# -*- coding: utf-8 -*-
import json
import transaction

from alembic import config, command
from csv import DictReader
from lxml import etree
from pkg_resources import resource_stream
from pyramid.paster import (get_appsettings, setup_logging)
from pywebtools.sqlalchemy import DBSession, Base
from pywebtools.pyramid.auth.models import User, PermissionGroup, Permission
from sqlalchemy import engine_from_config


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
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'ess:migrations')
    command.stamp(alembic_config, "head")
