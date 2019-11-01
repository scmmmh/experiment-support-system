"""
###############################################################
Fix single/multiple choice grid issues with before/after labels
###############################################################

Revision ID: 319a0b5f9c3d
Revises: 23b66139a952
Create Date: 2013-03-10 18:50:21.944204

# flake8: noqa
"""
from alembic import op
from json import dumps
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '319a0b5f9c3d'
down_revision = '23b66139a952'

metadata = sa.MetaData()
qtg = sa.Table('question_type_groups', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.Unicode(255)))
qt = sa.Table('question_types', metadata,
              sa.Column('group_id', sa.Integer),
              sa.Column('name', sa.Unicode(255)),
              sa.Column('backend', sa.UnicodeText),
              sa.Column('frontend', sa.UnicodeText))


def upgrade():
    metadata.bind = op.get_bind()
    core_qtg = op.get_bind().execute(qtg.select(qtg.c.name == 'core')).first()
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'single_choice_grid'),
                                    {'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'unicode',
                                                  'name': 'before_label',
                                                  'title': 'Before label',
                                                  'attr': 'further.before_label',
                                                  'default': None,
                                                  'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'unicode',
                                                  'name': 'after_label',
                                                  'title': 'After label',
                                                  'attr': 'further.after_label',
                                                  'default': None,
                                                  'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'table',
                                                  'name': 'answer',
                                                  'title': 'Answers',
                                                  'attr': 'answer',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'value',
                                                               'title': 'Value',
                                                               'attr': 'value',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}},
                                                 {'type': 'table',
                                                  'name': 'subquestion',
                                                  'title': 'Sub-questions',
                                                  'attr': 'subquestion',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'name',
                                                               'title': 'Name',
                                                               'attr': 'name',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}}]),
                                     'frontend': """<div py:attrs="{'class':error_class}">
  <table>
    <thead>
      <tr>
        <th></th>
        <th py:if="q.attr_value('further.before_label')"></th>
        <th py:for="label in q.attr_value('answer.label', default=[], multi=True)">${label}</th>
        <th py:if="q.attr_value('further.after_label')"></th>
      </tr>
    </thead>
    <tbody>
      <tr py:for="(sub_q_name, sub_q_label) in zip(q.attr_value('subquestion.name', default=[], multi=True), q.attr_value('subquestion.label', default=[], multi=True))">
        <th>${sub_q_label}</th>
        <th py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)">${f.radio('%s.%s' % (name, sub_q_name), value, None)}</td>
        <th py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <p py:if="error_text">${error_text}</p>
</div>"""}))
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'multi_choice_grid'),
                                    {'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'unicode',
                                                  'name': 'before_label',
                                                  'title': 'Before label',
                                                  'attr': 'further.before_label',
                                                  'default': None,
                                                  'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'unicode',
                                                  'name': 'after_label',
                                                  'title': 'After label',
                                                  'attr': 'further.after_label',
                                                  'default': None,
                                                  'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'table',
                                                  'name': 'answer',
                                                  'title': 'Answers',
                                                  'attr': 'answer',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'value',
                                                               'title': 'Value',
                                                               'attr': 'value',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}},
                                                 {'type': 'table',
                                                  'name': 'subquestion',
                                                  'title': 'Sub-questions',
                                                  'attr': 'subquestion',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'name',
                                                               'title': 'Name',
                                                               'attr': 'name',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}}]),
                                     'frontend': """<div py:attrs="{'class':error_class}">
  <table>
    <thead>
      <tr>
        <th></th>
        <th py:if="q.attr_value('further.before_label')"></th>
        <th py:for="label in q.attr_value('answer.label', default=[], multi=True)">${label}</th>
        <th py:if="q.attr_value('further.after_label')"></th>
      </tr>
    </thead>
    <tbody>
      <tr py:for="(sub_q_name, sub_q_label) in zip(q.attr_value('subquestion.name', default=[], multi=True), q.attr_value('subquestion.label', default=[], multi=True))">
        <th>${sub_q_label}</th>
        <th py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)">${f.checkbox('%s.%s' % (name, sub_q_name), value, None)}</td>
        <th py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <p py:if="error_text">${error_text}</p>
</div>"""}))


def downgrade():
    metadata.bind = op.get_bind()
    core_qtg = op.get_bind().execute(qtg.select(qtg.c.name==u'core')).first()
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id==core_qtg[0], qt.c.name==u'single_choice_grid'),
                                    {'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'table',
                                                  'name': 'answer',
                                                  'title': 'Answers',
                                                  'attr': 'answer',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'value',
                                                               'title': 'Value',
                                                               'attr': 'value',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}},
                                                 {'type': 'table',
                                                  'name': 'subquestion',
                                                  'title': 'Sub-questions',
                                                  'attr': 'subquestion',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'name',
                                                               'title': 'Name',
                                                               'attr': 'name',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}}]),
                                     'frontend': """<div py:attrs="{'class':error_class}">
  <table>
    <thead>
      <tr>
        <th></th>
        <th></th>
        <th py:for="label in q.attr_value('answer.label', default=[], multi=True)">${label}</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr py:for="(sub_q_name, sub_q_label) in zip(q.attr_value('subquestion.name', default=[], multi=True), q.attr_value('subquestion.label', default=[], multi=True))">
        <th>${sub_q_label}</th>
        <th py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)">${f.radio('%s.%s' % (name, sub_q_name), value, None)}</td>
        <th py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <p py:if="error_text">${error_text}</p>
</div>"""}))
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'multi_choice_grid'),
                                    {'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'table',
                                                  'name': 'answer',
                                                  'title': 'Answers',
                                                  'attr': 'answer',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'value',
                                                               'title': 'Value',
                                                               'attr': 'value',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}},
                                                 {'type': 'table',
                                                  'name': 'subquestion',
                                                  'title': 'Sub-questions',
                                                  'attr': 'subquestion',
                                                  'columns': [{'type': 'unicode',
                                                               'name': 'name',
                                                               'title': 'Name',
                                                               'attr': 'name',
                                                               'default': None,
                                                               'validator': {'not_empty': True}},
                                                              {'type': 'unicode',
                                                               'name': 'label',
                                                               'title': 'Label',
                                                               'attr': 'label',
                                                               'default': None,
                                                               'validator': {'not_empty': False}}],
                                                  'validator': {}}]),
                                     'frontend': """<div py:attrs="{'class':error_class}">
  <table>
    <thead>
      <tr>
        <th></th>
        <th></th>
        <th py:for="label in q.attr_value('answer.label', default=[], multi=True)">${label}</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr py:for="(sub_q_name, sub_q_label) in zip(q.attr_value('subquestion.name', default=[], multi=True), q.attr_value('subquestion.label', default=[], multi=True))">
        <th>${sub_q_label}</th>
        <th py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)">${f.checkbox('%s.%s' % (name, sub_q_name), value, None)}</td>
        <th py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <p py:if="error_text">${error_text}</p>
</div>"""}))
