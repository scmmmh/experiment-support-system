import click
import json
import transaction

from alembic import config, command
from pkg_resources import resource_string
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

#from ess.importexport import QuestionTypeIOSchema
from ..models.meta import Base
from ..models import get_engine


def init(subparsers):
    parser = subparsers.add_parser('initialise-database', help='Initialise the database')
    parser.add_argument('configuration', help='Experiment Support System configuration file')
    parser.add_argument('--drop-existing', action='store_true', default=False, help='Drop any existing tables')
    parser.set_defaults(func=initialise_database)


@click.argument('config-uri')
@click.option('--drop-existing', is_flag=True, default=False, help='false')
@click.command()
def create_database(config_uri, drop_existing):
    """Create (or re-create) the database"""
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = get_engine(settings)
    if drop_existing:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
