# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
from argparse import ArgumentParser

def get_user_parameter(prompt, default=''):
    if default:
        prompt = '%s [%s]: ' % (prompt, default)
    else:
        prompt = '%s: ' % (prompt)
    response = raw_input(prompt)
    if response.strip() == '':
        return default
    else:
        return response

def main():
    from . import configuration, populate, update

    parser = ArgumentParser(description='Experiment Support System administration application')
    subparsers = parser.add_subparsers()
    
    configuration.init(subparsers)
    populate.init(subparsers)
    update.init(subparsers)
    
    args = parser.parse_args()

    args.func(args)