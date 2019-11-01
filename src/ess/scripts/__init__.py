import click

from .configuration import generate_config
from .populate import create_database


@click.group()
def cli():
    """Run the Experiment Support System Admin CLI"""
    pass

cli.add_command(generate_config)
cli.add_command(create_database)
