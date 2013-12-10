# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from lxml import etree
from StringIO import StringIO

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
    if value:
        return value
    else:
        return default

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

def template_as_text(request, template, params, fmt, fancy_xml=False):
    from pywebtools.renderer import _genshi_loader 
    template = _genshi_loader.load(template)
    template = template.generate(**params)
    text = template.render(fmt)
    if fmt == 'xml' and fancy_xml:
        text = etree.tostring(etree.parse(StringIO(text), parser=etree.XMLParser(remove_blank_text=True)), pretty_print=True)
    return text

CACHED_SETTINGS = {}
def get_config_setting(request, key, target_type=None, default=None):
    global CACHED_SETTINGS
    if key in CACHED_SETTINGS:
        return CACHED_SETTINGS[key]
    else:
        if key in request.registry.settings:
            if target_type:
                CACHED_SETTINGS[key] = convert_type(request.registry.settings[key], target_type, default=default)
            else:
                CACHED_SETTINGS[key] = request.registry.settings[key]
        else:
            CACHED_SETTINGS[key] = default
        return get_config_setting(request, key, target_type=target_type, default=default)
    