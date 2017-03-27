# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from alembic import config, command

from ess.models import DB_VERSION

def init(subparsers):
    parser = subparsers.add_parser('update-database', help='Update the Experiment Support System database')
    parser.add_argument('configuration', help='Experiment Support System configuration file')
    parser.set_defaults(func=update_database)
    parser = subparsers.add_parser('downgrade-database', help='Downgrade the Experiment Support System database')
    parser.add_argument('configuration', help='Experiment Support System configuration file')
    parser.set_defaults(func=downgrade_database)


def update_database(args):
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'ess:migrations')
    alembic_config.set_section_option('app:main', 'url', 'hm')
    command.upgrade(alembic_config, DB_VERSION)


def downgrade_database(args):
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'ess:migrations')
    alembic_config.set_section_option('app:main', 'url', 'hm')
    command.downgrade(alembic_config, '-1')
