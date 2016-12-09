# -*- coding: utf-8 -*-
import json
import transaction

from alembic import config, command
from csv import DictReader
from lxml import etree
from pkg_resources import resource_stream
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

from ess.models import (DBSession, Base, Experiment, QSheet, DataItem,
                            DataItemAttribute, User,
                            QSheetAttribute, QSheetTransition,
                            DataSet, DataSetAttributeKey, Notification, PermutationSet,
                            DataSetRelation)

def init(subparsers):
    parser = subparsers.add_parser('initialise-database', help='Initialise the database')
    parser.add_argument('configuration', help='Experiment Support System configuration file')
    parser.add_argument('--drop-existing', action='store_true', default=False, help='Drop any existing tables')
    parser.set_defaults(func=initialise_database)
    parser = subparsers.add_parser('load-sample-data', help='Loads the sample data')
    parser.add_argument('configuration', help='Experiment Support System configuration file')
    parser.set_defaults(func=load_test_data)

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
        user = User(u'admin', u'admin@example.com', u'Admin', u'password')
        group = Group(title='Site administrator')
        group.permissions.append(Permission(name='admin.users', title='Administer the users'))
        group.permissions.append(Permission(name='admin.groups', title='Administer the permission groups'))
        group.permissions.append(Permission(name='admin.question_types', title='Administer the question types'))
        user.groups.append(group)
        group = Group(title='Developer')
        group.permissions.append(Permission(name='survey.new', title='Create new experiments'))
        user.groups.append(group)
        dbsession.add(user)
        group = Group(title='Content administrator')
        group.permissions.append(Permission(name='survey.view-all', title='View all experiments'))
        group.permissions.append(Permission(name='survey.edit-all', title='Edit all experiments'))
        group.permissions.append(Permission(name='survey.delete-all', title='Delete all experiments'))
        dbsession.add(group)
        element = XmlValidator().to_python(resource_stream('pyquest', 'scripts/templates/default_question_types.xml').read())
        dbsession.add(load_q_types_from_xml(dbsession, element, 0))
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'pyquest:migrations')
    command.stamp(alembic_config, "head")

def load_test_data(args):
    settings = get_appsettings(args.configuration)
    setup_logging(args.configuration)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    dbsession = DBSession()
    with transaction.manager:
        user = dbsession.query(User).first()
        
        # Sample Survey 1
        survey = load_survey_from_stream(resource_stream('pyquest', 'scripts/templates/sample_survey_1.exp'), user, dbsession)
        notification = Notification(ntype='interval', value=1, recipient=user.email)
        survey.notifications.append(notification)
        
        # Sample Survey 2
        survey = load_survey_from_stream(resource_stream('pyquest', 'scripts/templates/sample_survey_2.exp'), user, dbsession)
        notification = Notification(ntype='pcount', value=10, recipient=user.email)
        survey.notifications.append(notification)

        # Sample Survey 3
        load_survey_from_stream(resource_stream('pyquest', 'scripts/templates/sample_survey_3.exp'), user, dbsession)

        # SURVEY 4
        load_survey_from_stream(resource_stream('pyquest', 'scripts/templates/sample_survey_4.exp'), user, dbsession)
