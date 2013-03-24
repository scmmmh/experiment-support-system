# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
def convert_type(value, target_type, default=None):
    if target_type == 'int':
        try:
            return int(value)
        except ValueError:
            return default
    elif target_type == 'boolean':
        if value and value.lower() == 'true':
            return True
        else:
            return False
    return value

def load_question_schema_params(params, question):
    v_params = {}
    for key, value in params.items():
        if value['type'] == 'attr':
            v_params[key] = convert_type(question.attr_value(value['attr'], default=value['default'] if 'default' in value else None),
                                         value['data_type'] if 'data_type' in value else 'unicode',
                                         value['default'] if 'default' in value else None)
        elif value['type'] == 'value':
            v_params[key] = value['value']
    return v_params