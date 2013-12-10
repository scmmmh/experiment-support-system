# -*- coding: utf-8 -*-

import json
from genshi import Markup

from pywebtools import form, text

from pyquest.util import template_as_text, get_config_setting

def as_data_type(value, data_type=None):
    if data_type:
        if data_type == 'boolean':
            if value == 'True':
                return True
            else:
                return False
        elif data_type == 'js_boolean':
            if value == 'True':
                return 'true'
            else:
                return 'false'
        elif data_type == 'int':
            try:
                return int(value)
            except ValueError:
                return None
    else:
        return value

def gt():
    return Markup('>')

def gte():
    return Markup('>=')

def lt():
    return Markup('<')

def lte():
    return Markup('<=')