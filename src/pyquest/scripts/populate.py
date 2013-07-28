# -*- coding: utf-8 -*-

import transaction

from alembic import config, command
from csv import DictReader
from pkg_resources import resource_stream
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

from pyquest.models import (DBSession, Base, DataItem, DataItemAttribute, User,
                            Group, Permission, DataSet, DataSetAttributeKey,
                            Notification)
from pyquest.validation import XmlValidator
from pyquest.views.admin.question_types import load_q_types_from_xml
from pyquest.views.backend.qsheet import load_questions_from_xml
from pyquest.views.backend.survey import load_survey_from_xml

def init(subparsers):
    parser = subparsers.add_parser('initialise-database', help='Initialise the database')
    parser.add_argument('configuration', help='PyQuestionnaire configuration file')
    parser.add_argument('--drop-existing', action='store_true', default=False, help='Drop any existing tables')
    parser.set_defaults(func=initialise_database)
    parser = subparsers.add_parser('load-sample-data', help='Loads the sample data')
    parser.add_argument('configuration', help='PyQuestionnaire configuration file')
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
        group.permissions.append(Permission(name='survey.new', title='Create new surveys'))
        user.groups.append(group)
        dbsession.add(user)
        group = Group(title='Content administrator')
        group.permissions.append(Permission(name='survey.view-all', title='View all surveys'))
        group.permissions.append(Permission(name='survey.edit-all', title='Edit all surveys'))
        group.permissions.append(Permission(name='survey.delete-all', title='Delete all surveys'))
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
    def load_questions(qsheet, doc, DBSession):
        for item in doc:
            if item.tag == '{http://paths.sheffield.ac.uk/pyquest}questions':
                load_questions_from_xml(qsheet, item, DBSession, cleanup=False)
    dbsession = DBSession()
    with transaction.manager:
        user = dbsession.query(User).first()
        
        # Sample Survey 1
        element = XmlValidator().to_python(resource_stream('pyquest', 'scripts/templates/sample_survey_1.xml').read())
        survey = load_survey_from_xml(user, dbsession, element)
        dbsession.add(survey)
        notification = Notification(ntype='interval', value=1, recipient=user.email)
        survey.notifications.append(notification)
        
        # Sample Survey 2
        element = XmlValidator().to_python(resource_stream('pyquest', 'scripts/templates/sample_survey_2.xml').read())
        survey = load_survey_from_xml(user, dbsession, element)
        dbsession.add(survey)
        data_set = DataSet(name='test_samples', owned_by=user.id)
        data_set.survey = survey
        reader = DictReader(resource_stream('pyquest', 'scripts/templates/sample_survey_2.csv'))
        keys = {}
        for idx, column in enumerate(reader.fieldnames):
            if column != 'control_':
                attr_key = DataSetAttributeKey(key=column, order=idx)
                data_set.attribute_keys.append(attr_key)
                keys[column] = attr_key
        for line in reader:
            data_item = DataItem(data_set=data_set)
            for column, value in line.items():
                if column == 'control_':
                    if value.lower() == 'true' or value.lower() == 't' or value.lower() == '1':
                        data_item.control = True
                    else:
                        data_item.control = False
                else:
                    data_item.attributes.append(DataItemAttribute(key=keys[column], value=value))
        for qsheet in survey.qsheets:
            if qsheet.name == 'data':
                qsheet.data_set = data_set
        notification = Notification(ntype='pcount', value=10, recipient=user.email)
        survey.notifications.append(notification)
