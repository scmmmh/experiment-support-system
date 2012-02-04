# -*- coding: utf-8 -*-
'''
Created on 3 Feb 2012

@author: mhall
'''
from decorator import decorator
from formencode import validators, variabledecode
from formencode.schema import Schema
from lxml import etree
from StringIO import StringIO

from pyquest.helpers.qsheet import extract_choices

def qsheet_to_schema(qsheet):
    def process_element(element, f):
        if 'name' not in element.attrib:
            return {}
        schema = f(element)
        if 'required' in element.attrib and element.attrib['required'] == 'true':
            schema['required'] = True
        return {element.attrib['name']: schema}
    def process(element):
        if element.tag == u'{http://paths.sheffield.ac.uk/pyquest}qsheet':
            qschema = {}
            for child in element:
                qschema.update(process(child))
            return qschema
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}number':
            return process_element(element, number_input)
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}email':
            return process_element(element, lambda e: {'type': 'email'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}url':
            return process_element(element, lambda e: {'type': 'url'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}date':
            return process_element(element, lambda e: {'type': 'date'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}time':
            return process_element(element, lambda e: {'type': 'time'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}datetime':
            return process_element(element, lambda e: {'type': 'datetime'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}month':
            return process_element(element, lambda e: {'type': 'month'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}short_text':
            return process_element(element, lambda e: {'type': 'unicode'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}long_text':
            return process_element(element, lambda e: {'type': 'unicode'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}rating':
            return process_element(element, single_in_list)
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}rating_group':
            return process_element(element, grouped_single_in_list)
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}listchoice':
            return process_element(element, single_in_list)
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}selectchoice':
            return process_element(element, single_in_list)
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}multichoice':
            return process_element(element, multi_in_list)
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}multichoice_group':
            return process_element(element, grouped_multi_in_list)
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}confirm':
            return process_element(element, lambda e: {'type': 'boolean'})
        elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}ranking':
            return process_element(element, ranking)
        else:
            qschema = {}
            for child in element:
                qschema.update(process(child))
            return qschema
    doc = etree.parse(StringIO(qsheet))
    return process(doc.getroot())

def number_input(element):
    schema = {'type': 'number'}
    if 'required' in element.attrib and element.attrib['required'] == 'true':
        schema['required'] = True
    if 'min_value' in element.attrib:
        try:
            schema['min_value'] = int(element.attrib['min_value'])
        except ValueError:
            pass
    if 'max_value' in element.attrib:
        try:
            schema['max_value'] = int(element.attrib['max_value'])
        except ValueError:
            pass
    if 'step' in element.attrib:
        try:
            schema['step'] = int(element.attrib['step'])
        except ValueError:
            pass
    return schema

def single_in_list(element):
    return {'type': 'single_in_list',
            'values': map(lambda (v, _): v, extract_choices(element))}

def grouped_single_in_list(element):
    schema = {'type': 'compound', 'fields': {}}
    choices = extract_choices(element)
    for child in element:
        if child.tag == u'{http://paths.sheffield.ac.uk/pyquest}rating':
            if 'name' in child.attrib:
                schema['fields'][child.attrib['name']] = {'type': 'single_in_list',
                                                          'values': map(lambda (v, _): v, choices)}
    return schema

def multi_in_list(element):
    return {'type': 'multi_in_list',
            'values': map(lambda (v, _): v, extract_choices(element))}

def grouped_multi_in_list(element):
    schema = {'type': 'compound', 'fields': {}}
    choices = extract_choices(element)
    for child in element:
        if child.tag == u'{http://paths.sheffield.ac.uk/pyquest}multichoice':
            if 'name' in child.attrib:
                schema['fields'][child.attrib['name']] = {'type': 'multi_in_list',
                                                          'values': map(lambda (v, _): v, choices)}
    return schema

def ranking(element):
    return {'type': 'all_in_list',
            'values': map(lambda (v, _): v, extract_choices(element))}
    
class DynamicSchema(Schema):
    
    def __init__(self, source_schema):
        def not_empty(value):
            return 'required' in value and value['required']
        Schema.__init__(self)
        for (key, value) in source_schema.items():
            if value['type'] == 'compound':
                self.add_field(key, DynamicSchema(value['fields']))
            elif value['type'] == 'number':
                number_validator = validators.Number(not_empty=not_empty(value))
                if 'min_value' in value:
                    try:
                        number_validator.min = float(value['min_value'])
                    except ValueError:
                        pass
                if 'max_value' in value:
                    try:
                        number_validator.max = float(value['max_value'])
                    except ValueError:
                        pass
                self.add_field(key, number_validator)
            elif value['type'] == 'unicode':
                self.add_field(key, validators.UnicodeString(not_empty=not_empty(value)))
            elif value['type'] == 'email':
                self.add_field(key, validators.Email(not_empty=not_empty(value)))
            elif value['type'] == 'url':
                self.add_field(key, validators.URL(not_empty=not_empty(value)))
            elif value['type'] == 'date':
                pass
            elif value['type'] == 'time':
                pass
            elif value['type'] == 'datetime':
                pass
            elif value['type'] == 'month':
                pass
            elif value['type'] == 'single_in_list':
                pass
            elif value['type'] == 'multi_in_list':
                pass
            elif value['type'] == 'boolean':
                pass
            elif value['type'] == 'all_in_list':
                pass
            
class PageSchema(Schema):
    
    def __init__(self, qsheet_schema, items):
        Schema.__init__(self)
        items_schema = Schema()
        for item in items:
            if 'did' in item:
                items_schema.add_field(unicode(item['did']), DynamicSchema(qsheet_schema['fields']))
        self.add_field('items', items_schema)
    
    pre_validators = [variabledecode.NestedVariables()]
