"""Add styling markers to the *_choice question types.

Revision ID: 1cd78b756fb3
Revises: 305eb54c5d1c
Create Date: 2013-06-03 15:50:40.324668

"""

# revision identifiers, used by Alembic.
revision = '1cd78b756fb3'
down_revision = '305eb54c5d1c'

from alembic import op
import sqlalchemy as sa

qt_table = sa.sql.table('question_types',
                        sa.sql.column('id', sa.Integer),
                        sa.sql.column('name', sa.Unicode(255)),
                        sa.sql.column('frontend', sa.UnicodeText))

FRONTENDS = {u'single_choice': {u'new': u"""<div py:attrs="{'class':error_class}">
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
        <th py:if="q.attr_value('further.before_label')" class="before">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)" class="answer">${f.radio('%s.answer' % (name), value, None)}</td>
        <td py:if="q.attr_value('further.allow_other', 'no') == 'single'">${f.radio('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</td>
        <th py:if="q.attr_value('further.after_label')" class="after">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <ul py:if="q.attr_value('further.subtype', 'table') == 'list'">
    <li py:if="q.attr_value('further.before_label')" class="before">${q.attr_value('further.before_label')}</li>
    <li py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" class="answer">${f.radio('%s.answer' % (name), value, None, label=label)}</li>
    <li py:if="q.attr_value('further.allow_other', 'no') == 'single'" class="other">${f.radio('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</li>
    <li py:if="q.attr_value('further.after_label')" class="after">${q.attr_value('further.after_label')}</li>
  </ul>
  <div py:if="q.attr_value('further.subtype', 'table') == 'select'">
    <select name="${name}.answer" py:attrs="{'class': 'role-with-other' if q.attr_value('further.allow_other', 'no') == 'single' else None}">
      <option value="">--- Please choose ---</option>
      <option py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" value="${value}">${label}</option>
      <option py:if="q.attr_value('further.allow_other', 'no') == 'single'" value="_other">--- Other ---</option>
    </select>
    <py:if test="q.attr_value('further.allow_other', 'no') == 'single'">${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</py:if>
  </div>
  <p py:if="error_text" class="error-explanation">${error_text}</p>
</div>""", u'old': u"""<div py:attrs="{'class':error_class}">
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
</div>"""},
                u'multi_choice': {u'new': u"""<div py:attrs="{'class':error_class}">
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
        <th py:if="q.attr_value('further.before_label')" class="before">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)" class="answer">${f.checkbox('%s.answer' % (name), value, None)}</td>
        <td py:if="q.attr_value('further.allow_other', 'no') == 'single'" class="other">${f.checkbox('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</td>
        <th py:if="q.attr_value('further.after_label')" class="after">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <ul py:if="q.attr_value('further.subtype', 'table') == 'list'">
    <li py:if="q.attr_value('further.before_label')" class="before">${q.attr_value('further.before_label')}</li>
    <li py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" class="answer">${f.checkbox('%s.answer' % (name), value, None, label=label)}</li>
    <li py:if="q.attr_value('further.allow_other', 'no') == 'single'" class="other">${f.checkbox('%s.answer' % (name), '_other', None)}${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</li>
    <li py:if="q.attr_value('further.after_label')" class="after">${q.attr_value('further.after_label')}</li>
  </ul>
  <div py:if="q.attr_value('further.subtype', 'table') == 'select'">
    <select name="${name}.answer" multiple="multiple">
      <option py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" value="${value}">${label}</option>
    </select>
    <p py:if="q.attr_value('further.allow_other', 'no') == 'single'">Other: ${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</p>
  </div>
  <p py:if="error_text" class="error-explanation">${error_text}</p>
</div>""", u'old': u"""<div py:attrs="{'class':error_class}">
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
</div>"""},
                u'single_choice_grid': {u'new': u"""<div py:attrs="{'class':error_class}">
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
        <th class="sub-question">${sub_q_label}</th>
        <th py:if="q.attr_value('further.before_label')" class="before">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)" class="answer">${f.radio('%s.%s' % (name, sub_q_name), value, None)}</td>
        <th py:if="q.attr_value('further.after_label')" class="after">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <p py:if="error_text" class="error-explanation">${error_text}</p>
</div>""", u'old': u"""<div py:attrs="{'class':error_class}">
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
</div>"""},
                u'multi_choice_grid': {u'new': u"""<div py:attrs="{'class':error_class}">
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
        <th class="sub-question">${sub_q_label}</th>
        <th py:if="q.attr_value('further.before_label')" class="before">${q.attr_value('further.before_label')}</th>
        <td py:for="value in q.attr_value('answer.value', default=[], multi=True)" class="answer">${f.checkbox('%s.%s' % (name, sub_q_name), value, None)}</td>
        <th py:if="q.attr_value('further.after_label')" class="after">${q.attr_value('further.after_label')}</th>
      </tr>
    </tbody>
  </table>
  <p py:if="error_text" class="error-explanation">${error_text}</p>
</div>""", u'old': u"""<div py:attrs="{'class':error_class}">
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
</div>"""}}
def upgrade():
    for qt in op.get_bind().execute(qt_table.select().where(qt_table.c.name.in_(FRONTENDS.keys()))):
        op.get_bind().execute(qt_table.update().values(frontend=FRONTENDS[qt[1]]['new']).where(qt_table.c.id==qt[0]))

def downgrade():
    for qt in op.get_bind().execute(qt_table.select().where(qt_table.c.name.in_(FRONTENDS.keys()))):
        op.get_bind().execute(qt_table.update().values(frontend=FRONTENDS[qt[1]]['old']).where(qt_table.c.id==qt[0]))
