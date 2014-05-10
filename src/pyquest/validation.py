# -*- coding: utf-8 -*-
'''
Created on 3 Feb 2012

@author: mhall
'''
import cgi
import datetime
import re

from pkg_resources import resource_stream
from formencode import validators, variabledecode, foreach, compound, api
from formencode import FancyValidator, Schema, Invalid
from lxml import etree

from pyquest.util import convert_type, load_question_schema_params

schema = etree.XMLSchema(etree.parse(resource_stream('pyquest', 'static/experiment.xsd')))

class DateTimeValidator(FancyValidator):
    
    def __init__(self, date_type, **kwargs):
        FancyValidator.__init__(self, **kwargs)
        self.date_type = date_type
    
    def _to_python(self, value, state):
        if self.date_type == 'date':
            match = re.match(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})', value)
            if match:
                try:
                    return datetime.date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                except ValueError as ve:
                    raise Invalid(ve.message, value, state)
            else:
                raise Invalid('Please specify a valid date (dd/mm/yyyy).', value, state)
        elif self.date_type == 'time':
            match = re.match(r'([0-9]{1,2}):([0-9]{1,2})', value)
            if match:
                try:
                    return datetime.time(int(match.group(1)), int(match.group(2)))
                except ValueError as ve:
                    raise Invalid(ve.message, value, state)
            else:
                raise Invalid('Please specify a valid time (hh:mm).', value, state)
        elif self.date_type == 'datetime':
            match = re.match(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{4}) ([0-9]{2}):([0-9]{2})', value)
            if match:
                try:
                    return datetime.datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), int(match.group(4)), int(match.group(5)))
                except ValueError as ve:
                    raise Invalid(ve.message, value, state)
            else:
                raise Invalid('Please specify a valid date and time (dd/mm/yyyy hh:mm).', value, state)
        elif self.date_type == 'month':
            match = re.match(r'([0-9]{1,2})', value)
            if match:
                try:
                    value = int(value)
                    if value < 1 or value > 12:
                        raise Invalid('Please specify a valid month (1 - 12)', value, state)
                    return value
                except ValueError:
                    raise Invalid('Please specify a valid month (1 - 12)', value, state)
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
        raise Invalid('Invalid validation date_type', value, state)

class ChoiceValidator(FancyValidator):

    accept_iterator = True

    def __init__(self, values, allow_multiple, allow_other=False, **kwargs):
        FancyValidator.__init__(self, **kwargs)
        self.values = values
        self.allow_multiple = allow_multiple
        self.allow_other = allow_other == 'single'
        if self.allow_other:
            self.values.append('_other')

    def _to_python(self, value, state):
        if isinstance(value, dict):
            if 'answer' not in value:
                if self.not_empty:
                    raise Invalid('Please select your answer.', value, state)
                elif self.if_missing:
                    if self.allow_multiple:
                        return [self.if_missing]
                    else:
                        return self.if_missing
                    return None
                else:
                    return None
            answer = value['answer']
        else:
            answer = value
        if isinstance(answer, list):
            if not self.allow_multiple:
                raise Invalid('Please only select a single answer.', answer, state)
            for a in answer:
                if a not in self.values:
                    raise Invalid('Please only select valid answers..', answer, state)
            if '_other' in answer:
                answer.remove('_other')
                if self.not_empty and ('other' not in value or value['other'].strip() == ''):
                    raise Invalid('Please provide an "other" answer.', answer, state)
                answer.append(value['other'])
            else:
                if 'other' in value and value['other'].strip() != '':
                    raise Invalid('If you wish to provide an "other" answer, please select the Other option.', answer, state)
        else:
            if answer == '' and not self.not_empty:
                return ''
            if answer not in self.values:
                raise Invalid('Please select a valid answer.', answer, state)
            if answer == '_other':
                if self.not_empty and ('other' not in value or value['other'].strip() == ''):
                    raise Invalid('Please provide an "other" answer.', answer, state)
                answer = value['other']
            else:
                if 'other' in value and value['other'].strip() != '':
                    raise Invalid('If you wish to provide an "other" answer, please select the Other option.', answer, state)
        return answer
    
class RankingValidator(FancyValidator):
    
    accept_iterator = True
    messages = {'out-of-range': 'You must rank all items between %(min)i and %(max)i.'}
    
    def __init__(self, values, **kwargs):
        FancyValidator.__init__(self, **kwargs)
        self.values = values
        
    def _to_python(self, value, state):
        if not self.not_empty and value == self.if_missing:
            return {}
        for key in self.values:
            if key not in value:
                raise Invalid('You must rank all items.', value, state)
        result = {}
        ranks = [idx for idx in xrange(0, len(self.values))]
        for (key, value) in value.items():
            try:
                rank = int(value)
            except ValueError:
                if self.not_empty:
                    raise Invalid('You must rank all items.', value, state)
                else:
                    continue
            if rank < 0 or rank >= len(self.values):
                raise Invalid(self.message('out-of-range', state, min=1, max=len(self.values)), value, state)
            if rank not in ranks:
                raise Invalid('Each ranking may only be set for one item.', value, state)
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
                raise Invalid('Invalid CSRF token.', value, state)
        else:
            raise Invalid('Missing CSRF token.', value, state)

class XmlValidator(FancyValidator):
    
    namespace = u'https://bitbucket.org/mhall/experiment-support-system'
    
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

class FileReaderValidator(FancyValidator):

    def _to_python(self, value, state):
        if isinstance(value, cgi.FieldStorage):
            return ''.join(value.file)
        else:
            raise Invalid('No file was uploaded.', value, state)
    
class DynamicSchema(Schema):
    
    accept_iterator = True

    def __init__(self, **kwargs):
        Schema.__init__(self, **kwargs)

def validators_for_params(params, question):
    def augment(validator, question, missing_value=None):
        if question.required:
            validator.not_empty = True
            validator.if_missing = api.NoDefault
        else:
            validator.not_empty = False
            validator.if_missing = missing_value
        return validator
    v_params = {}
    if not params:
        return None
    if 'params' in params:
        v_params = load_question_schema_params(params['params'], question)
    if params['type'] == 'unicode':
        v_params['messages'] = {'empty': 'Please provide an answer to this question.',
                                'missingValue': 'Please provide an answer to this question.'}
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            return augment(foreach.ForEach(validators.UnicodeString(**v_params)), question)
        else:
            return augment(validators.UnicodeString(**v_params), question)
    elif params['type'] == 'number':
        v_params['messages'] = {'empty': 'Please provide an answer to this question.',
                                'missingValue': 'Please provide an answer to this question.',
                                'number': 'Please enter a number.',
                                'tooHigh': 'The number you entered is too high. The highest acceptable answer is %(max)s.',
                                'tooLow': 'The number you entered is too low. The lowest acceptable answer is %(min)s.'}
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            return augment(foreach.ForEach(validators.Number(**v_params)), question)
        else:
            return augment(validators.Number(**v_params), question)
    elif params['type'] == 'date':
        v_params['messages'] = {'empty': 'Please provide an answer to this question.',
                                'missingValue': 'Please provide an answer to this question.'}
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            return augment(foreach.ForEach(DateTimeValidator('date', **v_params)), question)
        else:
            return augment(DateTimeValidator('date', **v_params), question)
    elif params['type'] == 'time':
        v_params['messages'] = {'empty': 'Please provide an answer to this question.',
                                'missingValue': 'Please provide an answer to this question.'}
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            return augment(foreach.ForEach(DateTimeValidator('time', **v_params)), question)
        else:
            return augment(DateTimeValidator('time', **v_params), question)
    elif params['type'] == 'datetime':
        v_params['messages'] = {'empty': 'Please provide an answer to this question.',
                                'missingValue': 'Please provide an answer to this question.'}
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            return augment(foreach.ForEach(DateTimeValidator('datetime', **v_params)), question)
        else:
            return augment(DateTimeValidator('datetime', **v_params), question)
    elif params['type'] == 'month':
        v_params['messages'] = {'empty': 'Please provide an answer to this question.',
                                'missingValue': 'Please provide an answer to this question.'}
        if 'allow_multiple' in v_params and v_params['allow_multiple']:
            return augment(foreach.ForEach(DateTimeValidator('month', **v_params)), question)
        else:
            return augment(DateTimeValidator('month', **v_params), question)
    elif params['type'] == 'choice':
        v_params['messages'] = {'empty': 'Please select an answer to this question.',
                                'missingValue': 'Please select an answer to this question.'}
        return augment(ChoiceValidator(question.attr_value(params['attr'], multi=True, default=[]), **v_params), question)
    elif params['type'] == 'ranking':
        v_params['messages'] = {'empty': 'Please provide an answer to this question.',
                                'missingValue': 'Please provide an answer to this question.'}
        return augment(RankingValidator(question.attr_value(params['attr'], multi=True, default=[]), **v_params), question)
    elif params['type'] == 'multiple':
        schema = DynamicSchema(messages={'empty': 'Please provide an answer to this question.', 'missingValue': 'Please provide an answer to this question.'})
        for attr in question.attr_value(params['attr'], multi=True, default=[]):
            validator = validators_for_params(params['schema'], question)
            if validator:
                schema.add_field(attr, validator)
        return augment(schema, question)
    else:
        return augment(validators.UnicodeString(messages={'empty': 'Please provide an answer to this question.', 'missingValue': 'Please provide an answer to this question.'}), question)
    return None


class QuestionSchema(Schema):
    
    accept_iterator = True

    def __init__(self, questions, **kwargs):
        Schema.__init__(self, **kwargs)
        for question in questions:
            validator = validators_for_params(question.q_type.answer_schema(), question)
            if validator:
                self.add_field(question.name, validator)
            
class PageSchema(Schema):
    
    accept_iterator = True
    action_ = validators.UnicodeString()
    
    def __init__(self, qsheet, items, csrf_test=True):
        Schema.__init__(self)
        items_schema = Schema()
        for item in items:
            if 'did' in item:
                item_schema = QuestionSchema(qsheet.questions, messages={'empty': 'Please provide an answer to this question.', 'missingValue': 'Please provide an answer to this question.'})
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
                elif value.error_list:
                    for idx, value2 in enumerate(value.error_list):
                        sub_error = flatten_dict(value2)
                        if isinstance(sub_error, dict):
                            for (key3, value3) in sub_error.items():
                                result['%s-%i.%s' % (key, idx, key3)] = value3
                        else:
                            result['%s-%i' % (key, idx)] = sub_error
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

class QuestionTypeSchema(Schema):
    
    accept_iterator = True

    def __init__(self, schema, **kwargs):
        Schema.__init__(self, **kwargs)
        for field in schema:
            if field['type'] == 'question-name':
                self.add_field('name', compound.Pipe(validators=[validators.UnicodeString(not_empty=True),
                                                                 validators.Regex(r'^[a-zA-Z0-9_]+$', messages={'invalid':'Name must contain only letters, numbers and underscores.'})]))
            elif field['type'] == 'question-title':
                self.add_field('title', validators.UnicodeString(not_empty=True))
            elif field['type'] == 'question-help':
                self.add_field('help', validators.UnicodeString(if_missing='', if_empty='', not_empty=False))
            elif field['type'] == 'question-required':
                self.add_field('required', validators.StringBool(if_missing=False))
            else:
                if field['type'] in ['richtext', 'unicode']:
                    self.add_field(field['name'], validators.UnicodeString(**field['validator']))
                elif field['type'] == 'int':
                    self.add_field(field['name'], validators.Int(**field['validator']))
                elif field['type'] == 'select':
                    self.add_field(field['name'], validators.OneOf([v[0] for v in field['values']], **field['validator']))
                elif field['type'] == 'table':
                    sub_schema = QuestionTypeSchema(field['columns'], **field['validator'])
                    sub_schema.add_field('_order', validators.Int(not_empty=True))
                    self.add_field(field['name'], foreach.ForEach(sub_schema))
                
