"""
Script used to generate a configuration file.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import click
import uuid

from binascii import hexlify
from jinja2 import Environment, PackageLoader
from nacl.secret import SecretBox
from nacl.utils import random

from pkg_resources import resource_string


@click.argument('config-uri', type=click.File('w'))
@click.option('--title', default='Experiment Support System', help='Experiment Support System')
@click.option('--sqla-uri', default='sqlite:///%(here)s/ess.sqlite', help='sqlite:///%(here)s/ess.sqlite')
@click.option('--email-host', default='', help='')
@click.option('--host', default='127.0.0.1', help='127.0.0.1')
@click.option('--port', type=int, default=6543, help='6543')
@click.option('--debug', is_flag=True, default=False, help='false')
@click.command()
def generate_config(config_uri, title, sqla_uri, email_host, host, port, debug):
    """Generates a configuration file based on the default_config.txt template.
    """
    env = Environment(
        loader=PackageLoader('ess', 'scripts/templates')
    )
    template = env.get_template('default_config.txt')
    secret = hexlify(random(SecretBox.KEY_SIZE))
    config_uri.write(template.render(app_title=title,
                                     sqlalchemy_url=sqla_uri,
                                     email_host=email_host,
                                     session_key=secret.decode(),
                                     host=host,
                                     port=port,
                                     debug=debug))
