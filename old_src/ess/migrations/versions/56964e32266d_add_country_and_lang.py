"""
##################################
Add country and language questions
##################################

Revision ID: 56964e32266d
Revises: 36bdedebf543
Create Date: 2013-03-23 13:38:39.461584
# flake8: noqa
"""

# revision identifiers, used by Alembic.
revision = '56964e32266d'
down_revision = '36bdedebf543'

import sqlalchemy as sa

from alembic import op
from json import dumps

metadata = sa.MetaData()

qt = sa.Table('question_types', metadata,
                        sa.Column('id', sa.Integer),
                        sa.Column('name', sa.Unicode(255)),
                        sa.Column('title', sa.Unicode(255)),
                        sa.Column('dbschema', sa.UnicodeText),
                        sa.Column('answer_validation', sa.UnicodeText),
                        sa.Column('backend', sa.UnicodeText),
                        sa.Column('frontend', sa.UnicodeText),
                        sa.Column('group_id', sa.Integer))

qtg = sa.Table('question_type_groups', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.Unicode(255), unique=True),
               sa.Column('title', sa.Unicode(255)),
               sa.Column('order', sa.Integer))

def upgrade():
    metadata.bind = op.get_bind()
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name == 'core')).first()[0]
    op.get_bind().execute(qt.insert({'name': 'country',
                                     'title': 'Country selection',
                                     'dbschema': dumps([{'type': 'attr',
                                                         'attr': 'further.priority',
                                                         'default': '',
                                                         'group_order': 0},
                                                        {'type': 'attr',
                                                         'attr': 'further.allow_multiple',
                                                         'default': 'no',
                                                         'group_order': 1}]),
                                     'answer_validation': dumps({'type': 'unicode'}),
                                     'backend': dumps([{'type': 'question-name'},
                                                       {'type': 'question-title'},
                                                       {'type': 'question-help'},
                                                       {'type': 'question-required'},
                                                       {'type': 'unicode',
                                                        'name': 'priority',
                                                        'title': 'Prioritise these countries',
                                                        'attr': 'further.priority',
                                                        'default': '',
                                                        'validator': {'not_empty': False, 'if_empty': ''}},
                                                       {'type': 'select',
                                                        'name': 'multiple',
                                                        'title': 'Allow multiple selection',
                                                        'attr': 'further.allow_multiple',
                                                        'values': [('no', 'No'), ('yes', 'Yes')],
                                                        'default': 'no',
                                                        'validator': {}}]),
                                     'frontend': """<?python
    from babel import Locale
    locale = Locale('en')
    territories = locale.territories.items()
    territories.sort(key=lambda t:t[1])
?>
<select name="${name}" py:with="priority=[l.strip().upper() for l in q.attr_value('further.priority', default='').split(',') if l.strip()]" py:attrs="{'multiple': 'multiple' if q.attr_value('further.allow_multiple') == 'yes' else None}">
  <option value="" py:if="q.attr_value('further.allow_multiple') == 'no'">--- Please choose ---</option>
  <py:if test="priority">
    <option py:for="territory in territories" value="${territory[0]}" py:if="territory[0] in priority">${territory[1]}</option>
    <option value="" disabled="disabled">--------------------</option>
  </py:if>
  <option py:for="territory in territories" value="${territory[0]}" py:if="territory[0] not in priority">${territory[1]}</option>
</select>""",
                                     'group_id': qtg_id}))
    op.get_bind().execute(qt.insert({'name': u'language',
                                     'title': u'Language selection',
                                     'dbschema': dumps([{'type': 'attr',
                                                         'attr': 'further.priority',
                                                         'default': '',
                                                         'group_order': 0},
                                                        {'type': 'attr',
                                                         'attr': 'further.allow_multiple',
                                                         'default': 'no',
                                                         'group_order': 1}]),
                                     'answer_validation': dumps({'type': 'unicode'}),
                                     'backend': dumps([{'type': 'question-name'},
                                                       {'type': 'question-title'},
                                                       {'type': 'question-help'},
                                                       {'type': 'question-required'},
                                                       {'type': 'unicode',
                                                        'name': 'priority',
                                                        'title': 'Prioritise these languages',
                                                        'attr': 'further.priority', 'default': '',
                                                        'validator': {'not_empty': False, 'if_empty': ''}},
                                                       {'type': 'select',
                                                        'name': 'multiple',
                                                        'title': 'Allow multiple selection',
                                                        'attr': 'further.allow_multiple',
                                                        'values': [('no', 'No'), ('yes', 'Yes')],
                                                        'default': 'no',
                                                        'validator': {}}]),
                                     'frontend': """<?python
    from babel import Locale
    locale = Locale('en')
    languages = locale.languages.items()
    languages.sort(key=lambda t:t[1])
?>
<select name="${name}" py:with="priority=[l.strip().lower() for l in q.attr_value('further.priority', default='').split(',') if l.strip()]" py:attrs="{'multiple': 'multiple' if q.attr_value('further.allow_multiple') == 'yes' else None}">
  <option value="" py:if="q.attr_value('further.allow_multiple') == 'no'">--- Please choose ---</option>
  <py:if test="priority">
    <option py:for="language in languages" value="${language[0]}" py:if="language[0] in priority">${language[1]}</option>
    <option value="" disabled="disabled">--------------------</option>
  </py:if>
  <option py:for="language in languages" value="${language[0]}" py:if="language[0] not in priority">${language[1]}</option>
</select>""",
                                     'group_id': qtg_id}))


def downgrade():
    metadata.bind = op.get_bind()
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name == 'core')).first()[0]
    op.get_bind().execute(qt.delete().where(sa.and_(qt.c.group_id == qtg_id, qt.c.name == 'country')))
    op.get_bind().execute(qt.delete().where(sa.and_(qt.c.group_id == qtg_id, qt.c.name == 'language')))
