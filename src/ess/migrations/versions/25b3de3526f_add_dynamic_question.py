"""Add dynamic question type

Revision ID: 25b3de3526f
Revises: 105647470980
Create Date: 2012-11-18 19:17:40.887408

"""

# revision identifiers, used by Alembic.
revision = '25b3de3526f'
down_revision = '105647470980'

from alembic import op
from json import dumps
import sqlalchemy as sa

q_table = sa.sql.table('questions',
                       sa.sql.column('type', sa.Unicode(255)),
                       sa.sql.column('type_id', sa.Integer))
qt_table = sa.sql.table('question_types',
                        sa.sql.column('id', sa.Integer),
                        sa.sql.column('name', sa.Unicode(255)),
                        sa.sql.column('title', sa.Unicode(255)),
                        sa.sql.column('dbschema', sa.UnicodeText),
                        sa.sql.column('answer_validation', sa.UnicodeText),
                        sa.sql.column('backend', sa.UnicodeText),
                        sa.sql.column('frontend', sa.UnicodeText))

def upgrade():
    op.create_table('question_types',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.Unicode(255)),
                    sa.Column('title', sa.Unicode(255)),
                    sa.Column('dbschema', sa.UnicodeText),
                    sa.Column('answer_validation', sa.UnicodeText),
                    sa.Column('backend', sa.UnicodeText),
                    sa.Column('frontend', sa.UnicodeText))
    op.add_column('questions', sa.Column('type_id', sa.Integer, sa.ForeignKey('question_types.id', name='question_types_fk')))
    op.bulk_insert(qt_table, [{'name': 'text',
                               'title': 'Text',
                               'dbschema': dumps([{'type': 'attr', 'attr': 'text.text', 'default': 'Double-click to edit this text.'}]),
                               'answer_validation': dumps(None),
                               'backend': dumps([{'type': 'richtext', 'attr': 'text.text', 'name': 'text', 'validator': {'not_empty': False}}]),
                               'frontend': "${Markup(sub(q.attr_value('text.text'), i, p))}"},
                              {'name': 'short_text',
                               'title': 'Single-line text input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'unicode'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.text_field(name, '', e)}"},
                              {'name': 'long_text',
                               'title': 'Multi-line text input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'unicode'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.textarea(name, '', e)}"},
                              {'name': 'number',
                               'title': 'Number input',
                               'dbschema': dumps([{'type': 'attr', 'attr': 'further.min', 'default': None},
                                                  {'type': 'attr', 'attr': 'further.max', 'default': None}]),
                               'answer_validation': dumps({'type': 'number', 'params': {'min': {'type': 'attr', 'attr': 'further.min', 'data_type': 'int'}, 'max': {'type': 'attr', 'attr': 'further.max', 'data_type': 'int'}}}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'int', 'name': 'min', 'title': 'Minimum value', 'attr': 'further.min', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'int', 'name': 'max', 'title': 'Maximum value', 'attr': 'further.max', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}}]),
                               'frontend': "${f.number_field(name, '', e, min=q.attr_value('further.min'), max=q.attr_value('further.max'))}"},
                              {'name': 'email',
                               'title': 'E-Mail input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'email'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.email_field(name, '', e)}"},
                              {'name': 'url',
                               'title': 'URL input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'url'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.url_field(name, '', e)}"},
                              {'name': 'date',
                               'title': 'Date input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'date'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.date_field(name, '', e)}"},
                              {'name': 'time',
                               'title': 'Time input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'time'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.time_field(name, '', e)}"},
                              {'name': 'datetime',
                               'title': 'Date & Time input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'datetime'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.datetime_field(name, '', e)}"},
                              {'name': 'month',
                               'title': 'Month input',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'month'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'}]),
                               'frontend': "${f.month_field(name, '', e)}"},
                              {'name': 'single_choice',
                               'title': 'Single choice',
                               'dbschema': dumps([{'type': 'attr', 'attr': 'further.subtype', 'default': 'table', 'group_order': 0},
                                                  {'type': 'attr', 'attr': 'further.before_label', 'default': None, 'group_order': 1},
                                                  {'type': 'attr', 'attr': 'further.after_label', 'default': None, 'group_order': 1}]),
                               'answer_validation': dumps({'type': 'choice', 'attr': 'answer.value', 'params': {'allow_multiple': {'type': 'value', 'value': False},
                                                                                                                'allow_other': {'type': 'attr', 'attr': 'further.allow_other', 'default': 'no'}}}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'select', 'name': 'display', 'title': 'Display as', 'attr': 'further.subtype', 'values': [('table', 'Horizontal table'), ('list', 'Vertical list'), ('select', 'Select box')], 'default': 'table', 'validator': {}},
                                                 {'type': 'unicode', 'name': 'before_label', 'title': 'Before label', 'attr': 'further.before_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'unicode', 'name': 'after_label', 'title': 'After label', 'attr': 'further.after_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'table', 'name': 'answer', 'title': 'Answers', 'attr': 'answer', 'columns': [{'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'value', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                       {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}},
                                                 {'type': 'select', 'name': 'other', 'title': 'Allow other answers', 'attr': 'further.allow_other', 'values': [('no', 'No'), ('single', 'Yes')], 'default': 'no', 'validator': {}}]),
                               'frontend': """<div py:attrs="{'class':error_class}">
  <table py:if="q.attr_value('further.subtype', 'table') == 'table'">
    <thead>
      <tr>
        <th py:if="q.attr_value('further.before_label')"></th>
        <th py:for="label in q.attr_value('answer.label', default=[], multi=True)">${label}</th>
        <th py:if="q.attr_value('further.allow_other', 'no') == 'single'">Other</th>
        <th py:if="q.attr_value('further.after_label')"></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)">${f.radio('%s.answer' % (name), value, None)}</td>
        <td py:if="q.attr_value('further.allow_other', 'no') == 'single'">${f.radio('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</td>
        <th py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <ul py:if="q.attr_value('further.subtype', 'table') == 'list'">
    <li py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</li>
    <li py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))">${f.radio('%s.answer' % (name), value, None, label=label)}</li>
    <li py:if="q.attr_value('further.allow_other', 'no') == 'single'">${f.radio('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</li>
    <li py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</li>
  </ul>
  <div py:if="q.attr_value('further.subtype', 'table') == 'select'">
    <select name="${name}.answer">
      <option value="">--- Please choose ---</option>
      <option py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" value="${value}">${label}</option>
      <option py:if="q.attr_value('further.allow_other', 'no') == 'single'" value="_other">--- Other ---</option>
    </select>
    <py:if test="q.attr_value('further.allow_other', 'no') == 'single'">${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</py:if>
  </div>
  <p py:if="error_text">${error_text}</p>
</div>
"""},
                              {'name': 'multi_choice',
                               'title': 'Multiple choice',
                               'dbschema': dumps([{'type': 'attr', 'attr': 'further.subtype', 'default': 'table', 'group_order': 0},
                                                  {'type': 'attr', 'attr': 'further.before_label', 'default': None, 'group_order': 1},
                                                  {'type': 'attr', 'attr': 'further.after_label', 'default': None, 'group_order': 1}]),
                               'answer_validation': dumps({'type': 'choice', 'attr': 'answer.value', 'params': {'allow_multiple': {'type': 'value', 'value': True},
                                                                                                                'allow_other': {'type': 'attr', 'attr': 'further.allow_other', 'default': 'no'}}}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'select', 'name': 'display', 'title': 'Display as', 'attr': 'further.subtype', 'values': [('table', 'Horizontal table'), ('list', 'Vertical list'), ('select', 'Select box')], 'default': 'table', 'validator': {}},
                                                 {'type': 'unicode', 'name': 'before_label', 'title': 'Before label', 'attr': 'further.before_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'unicode', 'name': 'after_label', 'title': 'After label', 'attr': 'further.after_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                                 {'type': 'table', 'name': 'answer', 'title': 'Answers', 'attr': 'answer', 'columns': [{'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'value', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                       {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}},
                                                 {'type': 'select', 'name': 'other', 'title': 'Allow other answers', 'attr': 'further.allow_other', 'values': [('no', 'No'), ('single', 'Yes')], 'default': 'no', 'validator': {}}]),
                               'frontend': """<div py:attrs="{'class':error_class}">
  <table py:if="q.attr_value('further.subtype', 'table') == 'table'">
    <thead>
      <tr>
        <th py:if="q.attr_value('further.before_label')"></th>
        <th py:for="label in q.attr_value('answer.label', default=[], multi=True)">${label}</th>
        <th py:if="q.attr_value('further.allow_other', 'no') == 'single'">Other</th>
        <th py:if="q.attr_value('further.after_label')"></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)">${f.checkbox('%s.answer' % (name), value, None)}</td>
        <td py:if="q.attr_value('further.allow_other', 'no') == 'single'">${f.checkbox('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</td>
        <th py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <ul py:if="q.attr_value('further.subtype', 'table') == 'list'">
    <li py:if="q.attr_value('further.before_label')">${q.attr_value('further.before_label')}</li>
    <li py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))">${f.checkbox('%s.answer' % (name), value, None, label=label)}</li>
    <li py:if="q.attr_value('further.allow_other', 'no') == 'single'">${f.checkbox('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</li>
    <li py:if="q.attr_value('further.after_label')">${q.attr_value('further.after_label')}</li>
  </ul>
  <div py:if="q.attr_value('further.subtype', 'table') == 'select'">
    <select name="${name}.answer" multiple="multiple">
      <option py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" value="${value}">${label}</option>
      <option py:if="q.attr_value('further.allow_other', 'no') == 'single'" value="_other">--- Other ---</option>
    </select>
    <py:if test="q.attr_value('further.allow_other', 'no') == 'single'">${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</py:if>
  </div>
  <p py:if="error_text">${error_text}</p>
</div>
"""},
                              {'name': 'single_choice_grid',
                               'title': 'Single choice grid',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'multiple', 'attr': 'subquestion.name', 'schema': {'type': 'choice', 'attr': 'answer.value', 'params': {'allow_multiple': {'type': 'value', 'value': False},
                                                                                                                                                                           'allow_other': {'type': 'attr', 'attr': 'further.allow_other', 'default': 'no'}}}}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'table', 'name': 'answer', 'title': 'Answers', 'attr': 'answer', 'columns': [{'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'value', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                       {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}},
                                                 {'type': 'table', 'name': 'subquestion', 'title': 'Sub-questions', 'attr': 'subquestion', 'columns': [{'type': 'unicode', 'name': 'name', 'title': 'Name', 'attr': 'name', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                                       {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}}]),
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
</div>
"""},
                              {'name': 'multi_choice_grid',
                               'title': 'Multiple choice grid',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'multiple', 'attr': 'subquestion.name', 'schema': {'type': 'choice', 'attr': 'answer.value', 'params': {'allow_multiple': {'type': 'value', 'value': True},
                                                                                                                                                                           'allow_other': {'type': 'attr', 'attr': 'further.allow_other', 'default': 'no'}}}}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'table', 'name': 'answer', 'title': 'Answers', 'attr': 'answer', 'columns': [{'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'value', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                       {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}},
                                                 {'type': 'table', 'name': 'subquestion', 'title': 'Sub-questions', 'attr': 'subquestion', 'columns': [{'type': 'unicode', 'name': 'name', 'title': 'Name', 'attr': 'name', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                                       {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}}]),
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
</div>
"""},
                              {'name': 'confirm',
                               'title': 'Confirmation checkbox',
                               'dbschema': dumps([{'type': 'attr', 'attr': 'further.value', 'default': ''},
                                                  {'type': 'attr', 'attr': 'further.label', 'default': ''}]),
                               'answer_validation': dumps({'type': 'unicode'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'further.value', 'validator': {'not_empty': True}},
                                                 {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'further.label', 'validator': {'not_empty': True}}]),
                               'frontend': "${f.checkbox(name, q.attr_value('further.value'), e, label=q.attr_value('further.label', default=q.title))}"},
                              {'name': 'ranking',
                               'title': 'Ranking',
                               'dbschema': dumps([{'type': 'attr_group', 'name': 'answer'}]),
                               'answer_validation': dumps({'type': 'ranking', 'attr': 'answer.value'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-help'},
                                                 {'type': 'question-required'},
                                                 {'type': 'table', 'name': 'answer', 'title': 'Items', 'attr': 'answer', 'columns': [{'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'value', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                     {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}}]),
                               'frontend': """<div py:attrs="{'class':error_class}">
  <ul>
    <li py:if="q.attr_value('further.before_label')" class="role-label" style="display:none;">${q.attr_value('further.before_label')}</li>
    <li id="${name}.${value}" py:for="(value, label) in shuffle(zip(q.attr_value('answer.value', default=[], multi=True), q.attr_value('answer.label', default=[], multi=True)))">
      <select id="${name}.${value}-select" name="${name}.${value}">
        <option>--<py:if test="q.attr_value('further.before_label')"> ${q.attr_value('further.before_label')} --</py:if></option>
        <option py:for="idx in range(0, len(q.attr_value('answer.label', default=[], multi=True)))" value="${idx}">${idx + 1}</option>
        <option py:if="q.attr_value('further.after_label')">-- ${q.attr_value('further.after_label')} --</option>
      </select>
      <label for="${name}.${value}-item">${label}</label>
    </li>
    <li py:if="q.attr_value('further.after_label')" class="role-label" style="display:none;">${q.attr_value('further.after_label')}</li>
  </ul>
  <p py:if="error_text">${error_text}</p>
</div>
"""},
                              {'name': 'page_timer',
                               'title': 'Page Timer',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'int'}),
                               'backend': dumps([{'type': 'question-name'}]),
                               'frontend': """<script type="text/javascript">$(document).ready(function() {setTimeout(function() {var frm = $('form.role-survey-form'); frm.append('<input type="hidden" name="action_" value="Next Page"/>'); frm.submit();}, ${q.attr_value('further.timeout') * 1000})});</script>"""},
                              {'name': 'hidden_value',
                               'title': 'Hidden value',
                               'dbschema': dumps([{'type': 'attr', 'attr': 'further.value', 'default': ''}]),
                               'answer_validation': dumps({'type': 'unicode'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'further.value', 'default': '', 'validator': {'not_empty': True}}]),
                               'frontend': "${f.hidden_field(name, sub(q.attr_value('further.value'), i, p), None)}"},
                              {'name': 'js_check',
                               'title': 'JavaScript Check',
                               'dbschema': dumps([]),
                               'answer_validation': dumps({'type': 'unicode'}),
                               'backend': dumps([{'type': 'question-name'},
                                                 {'type': 'question-title'},
                                                 {'type': 'question-required'}]),
                               'frontend': """<noscript><p py:if="q.required">JavaScript is required</p><p py:if="not q.required">JavaScript is recommended</p></noscript>
<script>document.write('${f.hidden_field(name, 'yes', None)');</script>
"""},
                              {'name': 'auto_commit',
                               'title': 'Automatic Next Page',
                               'dbschema': dumps([{'type': 'attr', 'attr': 'further.timeout', 'default': '60'}]),
                               'answer_validation': dumps(None),
                               'backend': dumps([{'type': 'int', 'name': 'timeout', 'title': 'Timeout (seconds)', 'attr': 'further.timeout', 'default': '0', 'validator': {'not_empty': True}}]),
                               'frontend': "${f.hidden_field(name, '0', None, class_='role-timer')}"},])
    for qt in op.get_bind().execute(qt_table.select()):
        op.execute(q_table.update().where(q_table.c.type==qt[1]).values({'type_id': qt[0]}))
    op.drop_column('questions', 'type')
    

def downgrade():
    op.add_column('questions', sa.Column('type', sa.Unicode(255)))
    for qt in op.get_bind().execute(qt_table.select()):
        op.execute(q_table.update().where(q_table.c.type_id==qt[0]).values({'type': qt[1]}))
    op.drop_constraint('question_types_fk', 'questions', type='foreignkey')
    op.drop_column('questions', 'type_id')
    op.drop_table('question_types')
