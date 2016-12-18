import formencode

from pywebtools.formencode import CSRFSchema
from sqlalchemy import and_

from ess.models import Page


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


class QuestionEditSchema(CSRFSchema):

    def __init__(self, question, *args, **kwargs):
        CSRFSchema.__init__(self, *args, **kwargs)
        if question['display_as'] == 'text':
            self.add_field('text', formencode.validators.UnicodeString(if_empty='', if_missing=''))
        else:
            self.add_field('name', formencode.validators.UnicodeString)
