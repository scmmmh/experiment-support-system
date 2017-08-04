import transaction

from alembic import config, command
from pkg_resources import resource_string
from pyramid.paster import (get_appsettings, setup_logging)
from pywebtools.sqlalchemy import DBSession, Base
from pywebtools.pyramid.auth.models import User, PermissionGroup, Permission
from sqlalchemy import engine_from_config

from ess.importexport import QuestionTypeIOSchema


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
        question_types = QuestionTypeIOSchema(include_data=('q_type_group', 'parent', 'q_type_group.parent'),
                                              many=True).\
            loads(resource_string('ess', 'scripts/templates/default_question_types.json').decode('utf-8')).data
        for question_type in question_types:
            dbsession.add(question_type)
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'ess:migrations')
    command.stamp(alembic_config, "head")
