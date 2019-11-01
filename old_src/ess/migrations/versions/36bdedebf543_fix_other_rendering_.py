"""
####################################################
Fix other rendering on single/multi choide questions
####################################################

Revision ID: 36bdedebf543
Revises: 43ad0a13e1ea
Create Date: 2013-03-10 19:41:02.659131

# flake8: noqa
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36bdedebf543'
down_revision = '43ad0a13e1ea'

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
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'single_choice'),
                                    {'frontend': """<div py:attrs="{'class':error_class}">
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
    <select name="${name}.answer" py:attrs="{'class': 'role-with-other' if q.attr_value('further.allow_other', 'no') == 'single' else None}">
      <option value="">--- Please choose ---</option>
      <option py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" value="${value}">${label}</option>
      <option py:if="q.attr_value('further.allow_other', 'no') == 'single'" value="_other">--- Other ---</option>
    </select>
    <py:if test="q.attr_value('further.allow_other', 'no') == 'single'">${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</py:if>
  </div>
  <p py:if="error_text">${error_text}</p>
</div>"""}))
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'multi_choice'),
                                    {'frontend': """<div py:attrs="{'class':error_class}">
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
    </select>
    <p py:if="q.attr_value('further.allow_other', 'no') == 'single'">Other: ${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</p>
  </div>
  <p py:if="error_text">${error_text}</p>
</div>"""}))


def downgrade():
    metadata.bind = op.get_bind()
    core_qtg = op.get_bind().execute(qtg.select(qtg.c.name == 'core')).first()
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'single_choice'),
                                    {'frontend': """<div py:attrs="{'class':error_class}">
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
</div>"""}))
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'multi_choice'),
                                    {'frontend': """<div py:attrs="{'class':error_class}">
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
</div>"""}))
