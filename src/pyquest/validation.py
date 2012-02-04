# -*- coding: utf-8 -*-
'''
Created on 3 Feb 2012

@author: mhall
'''
import datetime
import re

from formencode import validators, variabledecode
from formencode import FancyValidator, Schema, Invalid
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
                if 'required' in element.attrib and element.attrib['required'] == 'true':
                    schema['fields'][child.attrib['name']]['required'] = True
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
                if 'required' in element.attrib and element.attrib['required'] == 'true':
                    schema['fields'][child.attrib['name']]['required'] = True
    return schema

def ranking(element):
    return {'type': 'all_in_list',
            'values': map(lambda (v, _): v, extract_choices(element))}

class DateTimeValidator(FancyValidator):
    
    def __init__(self, type, **kwargs):
        FancyValidator.__init__(self, **kwargs)
        self.type = type
    
    def _to_python(self, value, state):
        if self.type == 'date':
            match = re.match(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})', value)
            if match:
                try:
                    return datetime.date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                except ValueError as ve:
                    raise Invalid(ve.message, value, state)
            else:
                raise Invalid('Please specify a valid date', value, state)
        elif self.type == 'time':
            match = re.match(r'([0-9]{1,2}):([0-9]{1,2})', value)
            if match:
                try:
                    return datetime.time(int(match.group(1)), int(match.group(2)))
                except ValueError as ve:
                    raise Invalid(ve.message, value, state)
            else:
                raise Invalid('Please specify a valid time', value, state)
        elif self.type == 'datetime':
            match = re.match(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{4}) ([0-9]{2}):([0-9]{2})', value)
            if match:
                try:
                    return datetime.datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), int(match.group(4)), int(match.group(5)))
                except ValueError as ve:
                    raise Invalid(ve.message, value, state)
            else:
                raise Invalid('Please specify a valid date and time', value, state)
        elif self.type == 'month':
            match = re.match(r'([0-9]{1,2})', value)
            if match:
                value = int(value)
                if value < 1 or value > 12:
                    raise Invalid('Please specify a valid month', value, state)
                return value
            else:
                value = value.lower()
                if re.match(r'jan(uary)?', value):
                    return 1
                elif re.match(r'feb(ruary)?', value):
                    return 2
                elif re.match(r'mar(ch)?', value):
                    return 3
                elif re.match(r'apr(il)?', value):
                    return 4
                elif re.match(r'may', value):
                    return 5
                elif re.match(r'jun(e)?', value):
                    return 6
                elif re.match(r'jul(y)?', value):
                    return 7
                elif re.match(r'aug(ust)?', value):
                    return 8
                elif re.match(r'sep(tember)?', value):
                    return 9
                elif re.match(r'oct(ober)?', value):
                    return 10
                elif re.match(r'nov(ember)?', value):
                    return 11
                elif re.match(r'dec(ember)?', value):
                    return 12
        raise Invalid('Invalid validation type', value, state)

class RatingValidator(FancyValidator):
    
    messages = {'out-of-range': 'You must rank all values between %(min)i and %(max)i.'}
    
    def __init__(self, values, **kwargs):
        FancyValidator.__init__(self, **kwargs)
        self.values = values
        
    def _to_python(self, value, state):
        print '------'
        print self.not_empty
        print '--%s--' % self.if_missing
        print '--%s--' % value
        print self.if_missing == value
        if not self.not_empty and value == self.if_missing:
            return {}
        for key in self.values:
            if key not in value:
                raise Invalid('You must rank all items', value, state)
        result = {}
        for (key, value) in value.items():
            try:
                rank = int(value)
            except ValueError:
                raise Invalid('You must rank all items', value, state)
            if rank < 0 or rank >= len(self.values):
                raise Invalid(self.message('out-of-range', state, min=1, max=len(self.values)), value, state)
            result[key] = rank
        return result
    
class DynamicSchema(Schema):
    
    def __init__(self, source_schema, **kwargs):
        def augment(validator, value, missing_value=''):
            if 'required' in value and value['required']:
                validator.not_empty = True
            else:
                validator.not_empty = False
                validator.if_missing = missing_value
            return validator
        Schema.__init__(self, **kwargs)
        for (key, value) in source_schema.items():
            if value['type'] == 'compound':
                self.add_field(key, augment(DynamicSchema(value['fields']), value))
            elif value['type'] == 'number':
                number_validator = augment(validators.Number(), value)
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
                self.add_field(key, augment(validators.UnicodeString(), value))
            elif value['type'] == 'email':
                self.add_field(key, augment(validators.Email(), value))
            elif value['type'] == 'url':
                self.add_field(key, augment(validators.URL(), value))
            elif value['type'] == 'date':
                self.add_field(key, augment(DateTimeValidator('date'), value))
            elif value['type'] == 'time':
                self.add_field(key, augment(DateTimeValidator('time'), value))
            elif value['type'] == 'datetime':
                self.add_field(key, augment(DateTimeValidator('datetime'), value))
            elif value['type'] == 'month':
                self.add_field(key, augment(DateTimeValidator('month'), value))
            elif value['type'] == 'single_in_list':
                self.add_field(key, augment(validators.OneOf(value['values'], hideList=True), value))
            elif value['type'] == 'multi_in_list':
                self.add_field(key, augment(validators.OneOf(value['values'], hideList=True, testValueList=True), value))
            elif value['type'] == 'boolean':
                self.add_field(key, augment(validators.StringBool(), value, missing_value=False))
            elif value['type'] == 'all_in_list':
                self.add_field(key, augment(RatingValidator(value['values']), value))
            
class PageSchema(Schema):
    
    def __init__(self, qsheet_schema, items):
        Schema.__init__(self)
        items_schema = Schema()
        for item in items:
            if 'did' in item:
                items_schema.add_field(unicode(item['did']), DynamicSchema(qsheet_schema['fields']))
        self.add_field('items', items_schema)
    
    pre_validators = [variabledecode.NestedVariables()]
