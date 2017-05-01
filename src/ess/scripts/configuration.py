"""
Script used to generate a configuration file.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import uuid

from kajiki import TextTemplate
from pkg_resources import resource_string

from .main import get_user_parameter


def init(subparsers):
    parser = subparsers.add_parser('generate-config', help='Generate the Experiment Support System configuration file')
    parser.add_argument('--filename', default='production.ini', help='Configuration file name')
    parser.add_argument('--sqla-connection-string', default=None, help='SQLAlchemy database connection string')
    parser.add_argument('--debug', default=False, action='store_true', help='Set the debug flags in the configuration')
    parser.set_defaults(func=generate_config)


def generate_config(args):
    """Generates a configuration file based on the default_config.txt template.
    """
    tmpl = TextTemplate(resource_string('ess', 'scripts/templates/default_config.txt').decode('utf-8'))
    params = {'encrypt_key': uuid.uuid1(),
              'validate_key': uuid.uuid1(),
              'debug': args.debug}
    if args.sqla_connection_string:
        params['sqlalchemy_url'] = args.sqla_connection_string
    else:
        params['sqlalchemy_url'] = get_user_parameter('SQL Alchemy Connection String',
                                                      'sqlite:///%(here)s/eregisters_test.db')

    with open(args.filename, 'w') as out_f:
        out_f.write(tmpl(params).render())
