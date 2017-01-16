import formencode

from pywebtools.formencode import CSRFValidator
from sqlalchemy import and_

from ess.models import Page
from asyncio.test_utils import force_legacy_ssl_support


class PageNameUniqueValidator(formencode.FancyValidator):

    messages = {'page_exists': 'This name is already being used for a different page',
                'no_experiment': 'No experiment was specified to validate the Page',
                'no_dbsession': 'No dbsession was specified to validate the Page'}

    def _validate_python(self, value, state):
        if hasattr(state, 'dbsession'):
            if hasattr(state, 'experiment'):
                if state.dbsession.query(Page).filter(and_(Page.experiment == state.experiment,
                                                           Page.name == value)).first():
                    raise formencode.Invalid(self.message('page_exists', state), value, state)
            else:
                raise formencode.Invalid(self.message('no_experiment', state), value, state)
        else:
            raise formencode.Invalid(self.message('no_dbsession', state), value, state)


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
                        self.add_field(field['name'], formencode.foreach.ForEach(sub_validator, convert_to_list=True, **kwargs))
