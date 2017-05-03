import formencode
import re

from datetime import datetime
from pywebtools.formencode import CSRFValidator, CSRFSchema, DynamicSchema
from sqlalchemy import and_

from ess.models import Page, Question, DataSet
from ess.util import replace_variables


class PageExistsValidator(formencode.FancyValidator):

    messages = {'no_page': 'The selected page does not exist',
                'no_experiment': 'No experiment was specified to validate the Page',
                'no_dbsession': 'No dbsession was specified to validate the Page'}

    def _validate_python(self, value, state=None):
        if hasattr(state, 'dbsession'):
            if hasattr(state, 'experiment'):
                if not state.dbsession.query(Page).filter(and_(Page.experiment == state.experiment,
                                                               Page.id == value)).first():
                    raise formencode.Invalid(self.message('no_page', state), value, state)
            else:
                raise formencode.Invalid(self.message('no_experiment', state), value, state)
        else:
            raise formencode.Invalid(self.message('no_dbsession', state), value, state)

    def _convert_to_python(self, value, state=None):
        return int(value)


class PageNameUniqueValidator(formencode.FancyValidator):

    messages = {'page_exists': 'This name is already being used for a different page',
                'no_experiment': 'No experiment was specified to validate the page',
                'no_dbsession': 'No dbsession was specified to validate the page'}

    def _validate_python(self, value, state):
        if hasattr(state, 'dbsession'):
            if hasattr(state, 'experiment'):
                if hasattr(state, 'page_id'):
                    page = state.dbsession.query(Page).filter(and_(Page.id != state.page_id,
                                                                   Page.experiment == state.experiment,
                                                                   Page.name == value)).first()
                else:
                    page = state.dbsession.query(Page).filter(and_(Page.experiment == state.experiment,
                                                                   Page.name == value)).first()
                if page:
                    raise formencode.Invalid(self.message('page_exists', state), value, state)
            else:
                raise formencode.Invalid(self.message('no_experiment', state), value, state)
        else:
            raise formencode.Invalid(self.message('no_dbsession', state), value, state)


class QuestionExistsValidator(formencode.FancyValidator):

    messages = {'no_question': 'The selected question does not exist',
                'no_dbsession': 'No dbsession was specified to validate the page'}

    def __init__(self, page, *args, **kwargs):
        formencode.FancyValidator.__init__(self, *args, **kwargs)
        if isinstance(page, Page):
            self._page_id = page.id
        else:
            self._page_id = page

    def _validate_python(self, value, state=None):
        if hasattr(state, 'dbsession'):
            if not state.dbsession.query(Question).filter(and_(Question.page_id == self._page_id,
                                                               Question.id == value)).first():
                raise formencode.Invalid(self.message('no_question', state), value, state)
        else:
            raise formencode.Invalid(self.message('no_dbsession', state), value, state)

    def _convert_to_python(self, value, state=None):
        return int(value)


DATE_PATTERN = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}')


class DateValidator(formencode.FancyValidator):

    messages = {'invalid_format': 'Please enter the date as yyyy-mm-dd',
                'invalid_date': 'Please enter a valid date'}

    def _validate_python(self, value, state):
        match = DATE_PATTERN.match(value)
        if match:
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except:
                raise formencode.Invalid(self.message('invalid_date', state), value, state)
        else:
            raise formencode.Invalid(self.message('invalid_format', state), value, state)


TIME_PATTERN = re.compile('(([0-1][0-9])|(2[0-3])):[0-5][0-9]')


class TimeValidator(formencode.FancyValidator):

    messages = {'invalid_format': 'Please enter the time as hh:mm'}

    def _validate_python(self, value, state):
        if not TIME_PATTERN.match(value):
            raise formencode.Invalid(self.message('invalid_format', state), value, state)


DATETIME_PATTERN = re.compile('([0-9]{4}-[0-9]{2}-[0-9]{2})T(([0-1][0-9])|(2[0-3])):[0-5][0-9]Z')


class DateTimeValidator(formencode.FancyValidator):

    messages = {'invalid_format': 'Please enter the date-time as yyyy-mm-ddThh:mmZ',
                'invalid_date': 'Please enter a valid date'}

    def _validate_python(self, value, state):
        match = DATETIME_PATTERN.match(value)
        if match:
            try:
                datetime.strptime(value, '%Y-%m-%dT%H:%MZ')
            except:
                raise formencode.Invalid(self.message('invalid_date', state), value, state)
        else:
            raise formencode.Invalid(self.message('invalid_format', state), value, state)


MONTH_PATTERN = re.compile('[0-9]{4}-[0-9]{2}')


class MonthValidator(formencode.FancyValidator):

    messages = {'invalid_format': 'Please enter the month as yyyy-mm',
                'invalid_month': 'Please enter a valid month as a number, three letter abbreviation, or full month'}

    def _validate_python(self, value, state):
        match = MONTH_PATTERN.match(value)
        if match:
            try:
                datetime.strptime(value, '%Y-%m')
            except:
                raise formencode.Invalid(self.message('invalid_month', state), value, state)
        else:
            raise formencode.Invalid(self.message('invalid_format', state), value, state)


class DataSetUniqueValidator(formencode.FancyValidator):

    messages = {'data_set_exists': 'This name is already being used for a different data set',
                'no_experiment': 'No experiment was specified to validate the data set',
                'no_dbsession': 'No dbsession was specified to validate the data set'}

    def _validate_python(self, value, state):
        if hasattr(state, 'dbsession'):
            if hasattr(state, 'experiment'):
                data_set = state.dbsession.query(DataSet).filter(and_(DataSet.experiment == state.experiment,
                                                                      DataSet.name == value)).first()
                if data_set and (not hasattr(state, 'data_set') or state.data_set.id != data_set.id):
                    raise formencode.Invalid(self.message('data_set_exists', state), value, state)
            else:
                raise formencode.Invalid(self.message('no_experiment', state), value, state)
        else:
            raise formencode.Invalid(self.message('no_dbsession', state), value, state)


class DataSetExistsValidator(formencode.FancyValidator):

    messages = {'no_data_set': 'The selected data set does not exist',
                'no_experiment': 'No experiment was specified to validate the data set',
                'no_dbsession': 'No dbsession was specified to validate the data set'}

    def _validate_python(self, value, state=None):
        if hasattr(state, 'dbsession'):
            if hasattr(state, 'experiment'):
                if not state.dbsession.query(DataSet).filter(and_(DataSet.experiment_id == state.experiment.id,
                                                                  DataSet.id == value)).first():
                    raise formencode.Invalid(self.message('no_data_set', state), value, state)
            else:
                raise formencode.Invalid(self.message('no_experiment', state), value, state)
        else:
            raise formencode.Invalid(self.message('no_dbsession', state), value, state)

    def _convert_to_python(self, value, state=None):
        return int(value)


class QuestionEditSchema(formencode.Schema):

    pre_validators = [formencode.variabledecode.NestedVariables()]

    def __init__(self, fields, *args, csrf_validate=True, **kwargs):
        formencode.Schema.__init__(self, *args, **kwargs)
        if csrf_validate:
            self.add_field('csrf_token', CSRFValidator())
        for field in fields:
            if 'validation' in field:
                kwargs = {}
                for extra_arg in ['if_empty', 'if_missing', 'not_empty']:
                    if extra_arg in field['validation']:
                        kwargs[extra_arg] = field['validation'][extra_arg]
                if field['validation']['type'] == 'unicode':
                    self.add_field(field['name'], formencode.validators.UnicodeString(**kwargs))
                elif field['validation']['type'] == 'boolean':
                    self.add_field(field['name'], formencode.validators.StringBool(**kwargs))
                elif field['validation']['type'] == 'number':
                    self.add_field(field['name'], formencode.validators.Number(**kwargs))
                elif field['validation']['type'] == 'oneof':
                    self.add_field(field['name'], formencode.validators.OneOf(field['validation']['values'], **kwargs))
                elif field['validation']['type'] == 'nested':
                    self.add_field(field['name'], QuestionEditSchema(field['fields'], csrf_validate=False, **kwargs))
                elif field['validation']['type'] == 'foreach':
                    sub_validator = None
                    if field['validation']['sub_type'] == 'unicode':
                        sub_validator = formencode.validators.UnicodeString(**kwargs)
                    elif field['validation']['sub_type'] == 'nested':
                        sub_validator = QuestionEditSchema(field['fields'], csrf_validate=False, **kwargs)
                    if sub_validator:
                        self.add_field(field['name'],
                                       formencode.foreach.ForEach(sub_validator, convert_to_list=True, **kwargs))


class UserAgentSchema(formencode.Schema):

    input_type = formencode.ForEach(formencode.validators.OneOf(['mouse', 'touch', 'keyboard']),
                                    convert_to_list=True)
    screen_size = formencode.validators.UnicodeString(if_missing=None, if_empty=None)


class FrontendPageSchema(CSRFSchema):

    _user_agent = UserAgentSchema(if_missing={}, if_empty={})

    pre_validators = [formencode.variabledecode.NestedVariables()]
    messages = {'missingValue': 'Please answer this question'}

    def __init__(self, questions, data_items, actions, *args, **kwargs):
        formencode.Schema.__init__(self, *args, **kwargs)
        self.add_field('_action', formencode.validators.OneOf(actions, not_empty=True))
        if [True for q in questions if q['frontend', 'generates_response']]:
            for data_item in data_items:
                di_schema = DynamicSchema(messages=self._messages)
                for question in questions:
                    # Set the generic validation settings
                    default_attrs = {}
                    if question['frontend', 'required']:
                        default_attrs['not_empty'] = True
                        default_attrs['if_missing'] = formencode.NoDefault
                        default_attrs['if_empty'] = formencode.NoDefault
                    else:
                        default_attrs['if_missing'] = None
                        default_attrs['if_empty'] = None
                    if question['frontend', 'display_as'] == 'simple_input':
                        # Simple input field validation
                        if question['frontend', 'input_type'] == 'number':
                            di_schema.add_field(question['frontend', 'name'],
                                                formencode.validators.Number(**default_attrs))
                        elif question['frontend', 'input_type'] == 'email':
                            di_schema.add_field(question['frontend', 'name'],
                                                formencode.validators.Email(**default_attrs))
                        elif question['frontend', 'input_type'] == 'url':
                            di_schema.add_field(question['frontend', 'name'],
                                                formencode.validators.URL(**default_attrs))
                        elif question['frontend', 'input_type'] == 'date':
                            di_schema.add_field(question['frontend', 'name'], DateValidator(**default_attrs))
                        elif question['frontend', 'input_type'] == 'time':
                            di_schema.add_field(question['frontend', 'name'], TimeValidator(**default_attrs))
                        elif question['frontend', 'input_type'] == 'datetime':
                            di_schema.add_field(question['frontend', 'name'], DateTimeValidator(**default_attrs))
                        elif question['frontend', 'input_type'] == 'month':
                            di_schema.add_field(question['frontend', 'name'], MonthValidator(**default_attrs))
                        else:
                            di_schema.add_field(question['frontend', 'name'],
                                                formencode.validators.UnicodeString(**default_attrs))
                    elif question['frontend', 'display_as'] == 'select_simple_choice':
                        # Single / multi-choice validation
                        values = [replace_variables(answer['value'], question, data_item)
                                  for answer in question['frontend', 'answers']]
                        if question['frontend', 'allow_multiple']:
                            if question['frontend', 'allow_other']:
                                di_schema.add_field(question['frontend', 'name'],
                                                    formencode.compound.Any(DynamicSchema([('response',
                                                                                            formencode.foreach.ForEach(formencode.validators.OneOf(values + ['other']),  # noqa: E501
                                                                                                                       use_list=True,  # noqa: E501
                                                                                                                       **default_attrs)),  # noqa: E501
                                                                                           ('other', formencode.validators.UnicodeString(**default_attrs))]),  # noqa: E501
                                                                            DynamicSchema([('response',
                                                                                            formencode.foreach.ForEach(formencode.validators.OneOf(values),  # noqa: E501
                                                                                                                       use_list=True,  # noqa: E501
                                                                                                                       **default_attrs)),  # noqa: E501
                                                                                           ('other', formencode.validators.OneOf(['']))])))  # noqa: E501
                            else:
                                di_schema.add_field(question['frontend', 'name'],
                                                    formencode.foreach.ForEach(formencode.validators.OneOf(values),
                                                                               use_list=True,
                                                                               **default_attrs))
                        else:
                            if question['frontend', 'allow_other']:
                                di_schema.add_field(question['frontend', 'name'],
                                                    formencode.compound.Any(DynamicSchema([('response', formencode.validators.OneOf(values + ['other'])),  # noqa: E501
                                                                                           ('other', formencode.validators.UnicodeString(**default_attrs))]),  # noqa: E501
                                                                            DynamicSchema([('response', formencode.validators.OneOf(values)),  # noqa: E501
                                                                                           ('other', formencode.validators.OneOf(''))])))  # noqa: E501
                            else:
                                di_schema.add_field(question['frontend', 'name'],
                                                    formencode.validators.OneOf(values,
                                                                                **default_attrs))
                    elif question['frontend', 'display_as'] == 'select_grid_choice':
                        # Grid-structured single / multi-choice validation
                        values = [replace_variables(answer['value'], question, data_item)
                                  for answer in question['frontend', 'answers']]
                        sub_schema = DynamicSchema(messages={'missingValue': 'Please answer this question'},
                                                   **default_attrs)
                        for sub_question in question['frontend', 'questions']:
                            if question['frontend', 'allow_multiple']:
                                sub_schema.add_field(sub_question['name'],
                                                     formencode.foreach.ForEach(formencode.validators.OneOf(values),
                                                                                use_list=True,
                                                                                **default_attrs))
                            else:
                                sub_schema.add_field(sub_question['name'], formencode.validators.OneOf(values,
                                                                                                       **default_attrs))
                        di_schema.add_field(question['frontend', 'name'], sub_schema)
                    elif question['frontend', 'display_as'] == 'ranking':
                        # Ranking validation
                        values = [replace_variables(answer['value'], question, data_item)
                                  for answer in question['frontend', 'answers']]
                        di_schema.add_field(question['frontend', 'name'],
                                            formencode.validators.OneOf(values,
                                                                        testValueList=True,
                                                                        use_list=True,
                                                                        **default_attrs))
                self.add_field('d%s' % data_item.id, di_schema)
