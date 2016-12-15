import formencode

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
