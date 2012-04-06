# -*- coding: utf-8 -*-
'''
Created on 3 Feb 2012

@author: mhall
'''
import datetime
import re

from pkg_resources import resource_stream
from formencode import validators, variabledecode
from formencode import FancyValidator, Schema, Invalid
from lxml import etree

from pyquest.helpers.qsheet import get_q_attr_value, get_qg_attr_value, get_attr_groups


schema = etree.XMLSchema(etree.parse(resource_stream('pyquest', 'static/survey.xsd')))

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
                try:
                    value = int(value)
                    if value < 1 or value > 12:
                        raise Invalid('Please specify a valid month', value, state)
                    return value
                except ValueError:
                    raise Invalid('Please specify a valid month', value, state)
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

class RankingValidator(FancyValidator):
    
    messages = {'out-of-range': 'You must rank all values between %(min)i and %(max)i.'}
    
    def __init__(self, values, **kwargs):
        FancyValidator.__init__(self, **kwargs)
        self.values = values
        
    def _to_python(self, value, state):
        if not self.not_empty and value == self.if_missing:
            return {}
        for key in self.values:
            if key not in value:
                raise Invalid('You must rank all items', value, state)
        result = {}
        ranks = [idx for idx in xrange(0, len(self.values))]
        for (key, value) in value.items():
            try:
                rank = int(value)
            except ValueError:
                if self.not_empty:
                    raise Invalid('You must rank all items', value, state)
                else:
                    continue
            if rank < 0 or rank >= len(self.values):
                raise Invalid(self.message('out-of-range', state, min=1, max=len(self.values)), value, state)
            if rank not in ranks:
                raise Invalid('Each ranking may only be set for one item', value, state)
            else:
                ranks.remove(rank)
            result[key] = rank
        return result

class CsrfTokenValidator(FancyValidator):
    
    def _to_python(self, value, state):
        if state:
            try:
                return state.request.session.get_csrf_token()
            except AttributeError:
                raise Invalid('Invalid CSRF token', value, state)
        else:
            raise Invalid('Missing CSRF token', value, state)

class XmlValidator(FancyValidator):
    
    def __init__(self, wrapper='%s', **kwargs):
        FancyValidator.__init__(self, **kwargs)
        self.wrapper = wrapper
        
    def _to_python(self, value, state):
        try:
            doc = etree.fromstring(self.wrapper % value)
            schema.assertValid(doc)
            return doc
        except etree.XMLSyntaxError as xse:
            raise Invalid(unicode(xse), value, state)
        except etree.DocumentInvalid as de:
            raise Invalid(unicode(de), value, state)
    
class DynamicSchema(Schema):
    
    def __init__(self, questions, **kwargs):
        def augment(validator, question, missing_value=None):
            if question.required:
                validator.not_empty = True
            else:
                validator.not_empty = False
                validator.if_missing = missing_value
            return validator
        Schema.__init__(self, **kwargs)
        for question in questions:
            if question.type in ['short_text', 'long_text']:
                self.add_field(question.name, augment(validators.UnicodeString(), question))
            elif question.type == 'number':
                number_validator = augment(validators.Number(), question)
                if get_q_attr_value(question, 'further.min') and get_q_attr_value(question, 'further.min') != '': #TODO: Proper validation needed
                    number_validator.min = int(get_q_attr_value(question, 'further.min'))
                if get_q_attr_value(question, 'further.max') and get_q_attr_value(question, 'further.max') != '': #TODO: Proper validation needed
                    number_validator.max = int(get_q_attr_value(question, 'further.max'))
                self.add_field(question.name, number_validator)
            elif question.type == 'email':
                self.add_field(question.name, augment(validators.Email(), question))
            elif question.type == 'url':
                self.add_field(question.name, augment(validators.URL(), question))
            elif question.type in ['date', 'time', 'datetime', 'month']:
                self.add_field(question.name, augment(DateTimeValidator(question.type), question))
            elif question.type in ['rating', 'single_list', 'single_select']:
                values = [get_qg_attr_value(qg, 'value') for qg in get_attr_groups(question, 'answer')]
                self.add_field(question.name, augment(validators.OneOf(values, hideList=True), question))
            elif question.type == 'rating_group':
                values = [get_qg_attr_value(qg, 'value') for qg in get_attr_groups(question, 'answer')]
                sub_schema = DynamicSchema([])
                for sub_question in get_attr_groups(question, 'subquestion'):
                    sub_schema.add_field(get_qg_attr_value(sub_question, 'name'), augment(validators.OneOf(values, hideList=True), question))
                self.add_field(question.name, augment(sub_schema, question))
            elif question.type == 'confirm':
                self.add_field(question.name, augment(validators.UnicodeString(), question, missing_value=None))
            elif question.type == 'multichoice':
                values = [get_qg_attr_value(qg, 'value') for qg in get_attr_groups(question, 'answer')]
                self.add_field(question.name, augment(validators.OneOf(values, hideList=True, testValueList=True), question))
            elif question.type == 'multichoice_group':
                values = [get_qg_attr_value(qg, 'value') for qg in get_attr_groups(question, 'answer')]
                sub_schema = DynamicSchema([])
                for sub_question in get_attr_groups(question, 'subquestion'):
                    sub_schema.add_field(get_qg_attr_value(sub_question, 'name'), augment(validators.OneOf(values, hideList=True, testValueList=True), question))
                self.add_field(question.name, augment(sub_schema, question))
            elif question.type == 'ranking':
                values = [get_qg_attr_value(qg, 'value') for qg in get_attr_groups(question, 'answer')]
                self.add_field(question.name, augment(RankingValidator(values), question))
            
class PageSchema(Schema):
    
    action_ = validators.UnicodeString()
    
    def __init__(self, qsheet, items, csrf_test=True):
        Schema.__init__(self)
        items_schema = Schema()
        for item in items:
            if 'did' in item:
                item_schema = DynamicSchema(qsheet.questions)
                if csrf_test:
                    item_schema.add_field('csrf_token_', CsrfTokenValidator(not_empty=True))
                items_schema.add_field(unicode(item['did']), item_schema)
        self.add_field('items', items_schema)
    
    pre_validators = [variabledecode.NestedVariables()]

def flatten_invalid(ie, message='Unfortunately not all your answers were acceptable'):
    def flatten_dict(e):
        result = {}
        if e and e.error_dict:
            for (key, value) in e.error_dict.items():
                if value.error_dict:
                    for (key2, value2) in flatten_dict(value).items():
                        result['%s.%s' % (key, key2)] = value2
                else:
                    result[key] = unicode(value)
        return result
    return Invalid(message,
                   ie.value,
                   ie.state,
                   error_dict=flatten_dict(ie))

class ValidationState(object):
    
    def __init__(self, **kwargs):
        self.key = None
        self.full_dict = None
        self.index = None
        self.full_list = None
        for (key, value) in kwargs.items():
            self.__setattr__(key, value)
        