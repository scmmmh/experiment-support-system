# -*- coding: utf-8 -*-

import json

from pywebtools import form, text

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