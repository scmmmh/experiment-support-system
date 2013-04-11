# -*- coding: utf-8 -*-

try:
    import cPickle as pickle
except:
    import pickle
import os
import sys
import transaction

from alembic.config import Config
from alembic import command
from json import dumps
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config
from lxml import etree

from pyquest.models import (DBSession, Base, Survey, QSheet, DataItem,
                            DataItemAttribute, User, Group, Permission,
                            Question, QSheetTransition, QSheetAttribute,
                            DataItemControlAnswer, QuestionType,
                            QuestionTypeGroup)
from pyquest.views.backend.qsheet import load_questions_from_xml

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [--no-test-data]\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    init_data(DBSession)
    alembic_cfg = Config(config_uri)
    command.stamp(alembic_cfg, "head")
    if len(argv) > 2 and argv[2] == '--with-test-data':
        init_test_data(DBSession)

DEFAULT_QUESTIONS = [{'name': 'text',
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
    <select name="${name}.answer" py:attrs="{'class': 'role-with-other' if q.attr_value('further.allow_other', 'no') == 'single' else None}">
      <option value="">--- Please choose ---</option>
      <option py:for="(label, value) in zip(q.attr_value('answer.label', default=[], multi=True), q.attr_value('answer.value', default=[], multi=True))" value="${value}">${label}</option>
      <option py:if="q.attr_value('further.allow_other', 'no') == 'single'" value="_other">--- Other ---</option>
    </select>
    <py:if test="q.attr_value('further.allow_other', 'no') == 'single'">${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</py:if>
  </div>
  <p py:if="error_text">${error_text}</p>
</div>"""},
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
    </select>
    <p py:if="q.attr_value('further.allow_other', 'no') == 'single'">Other: ${f.text_field('%s.other' % (name), '', None, class_='role-other-text')}</p>
  </div>
  <p py:if="error_text">${error_text}</p>
</div>"""},
                     {'name': 'single_choice_grid',
                      'title': 'Single choice grid',
                      'dbschema': dumps([]),
                      'answer_validation': dumps({'type': 'multiple', 'attr': 'subquestion.name', 'schema': {'type': 'choice', 'attr': 'answer.value', 'params': {'allow_multiple': {'type': 'value', 'value': False},
                                                                                                                                                                  'allow_other': {'type': 'attr', 'attr': 'further.allow_other', 'default': 'no'}}}}),
                      'backend': dumps([{'type': 'question-name'},
                                        {'type': 'question-title'},
                                        {'type': 'question-help'},
                                        {'type': 'question-required'},
                                        {'type': 'unicode', 'name': 'before_label', 'title': 'Before label', 'attr': 'further.before_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                        {'type': 'unicode', 'name': 'after_label', 'title': 'After label', 'attr': 'further.after_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                        {'type': 'table', 'name': 'answer', 'title': 'Answers', 'attr': 'answer', 'columns': [{'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'value', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                              {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}},
                                        {'type': 'table', 'name': 'subquestion', 'title': 'Sub-questions', 'attr': 'subquestion', 'columns': [{'type': 'unicode', 'name': 'name', 'title': 'Name', 'attr': 'name', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                              {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}}]),
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
                                        {'type': 'unicode', 'name': 'before_label', 'title': 'Before label', 'attr': 'further.before_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                        {'type': 'unicode', 'name': 'after_label', 'title': 'After label', 'attr': 'further.after_label', 'default': None, 'validator': {'not_empty': False, 'if_empty': None}},
                                        {'type': 'table', 'name': 'answer', 'title': 'Answers', 'attr': 'answer', 'columns': [{'type': 'unicode', 'name': 'value', 'title': 'Value', 'attr': 'value', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                              {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}},
                                        {'type': 'table', 'name': 'subquestion', 'title': 'Sub-questions', 'attr': 'subquestion', 'columns': [{'type': 'unicode', 'name': 'name', 'title': 'Name', 'attr': 'name', 'default': None, 'validator': {'not_empty': True}},
                                                                                                                                              {'type': 'unicode', 'name': 'label', 'title': 'Label', 'attr': 'label', 'default': None, 'validator': {'not_empty': False}}], 'validator': {}}]),
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
                      'frontend': """${f.hidden_field(name, '0', class_='role-timer')}"""},
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
                      'frontend': """<script type="text/javascript">$(document).ready(function() {setTimeout(function() {var frm = $('form.role-survey-form'); frm.append('<input type="hidden" name="action_" value="Next Page"/>'); frm.submit();}, ${q.attr_value('further.timeout') * 1000})});</script>"""},
                     {'name': u'country',
                      'title': u'Country selection',
                      'dbschema': dumps([{'type': 'attr', 'attr': 'further.priority', 'default': '', 'group_order': 0},
                                         {'type': 'attr', 'attr': 'further.allow_multiple', 'default': 'no', 'group_order': 1}]),
                      'answer_validation': dumps({'type': 'unicode', 'params': {'allow_multiple': {'type': 'attr', 'attr': 'further.allow_multiple', 'default': False, 'data_type': 'boolean'}}}),
                      'backend': dumps([{'type': 'question-name'},
                                        {'type': 'question-title'},
                                        {'type': 'question-help'},
                                        {'type': 'question-required'},
                                        {'type': 'unicode', 'name': 'priority', 'title': 'Prioritise these countries', 'attr': 'further.priority', 'default': '', 'validator': {'not_empty': False, 'if_empty': ''}},
                                        {'type': 'select', 'name': 'multiple', 'title': 'Allow multiple selection', 'attr': 'further.allow_multiple', 'values': [('False', 'No'), ('True', 'Yes')], 'default': 'False', 'validator': {}}]),
                      'frontend': """<?python
    from babel import Locale
    locale = Locale('en')
    territories = locale.territories.items()
    territories.sort(key=lambda t:t[1])
?>
<select name="${name}" py:with="priority=[l.strip().upper() for l in q.attr_value('further.priority', default='').split(',') if l.strip()]" py:attrs="{'multiple': 'multiple' if q.attr_value('further.allow_multiple', default=False, data_type='boolean') else None}">
  <option value="" py:if="not q.attr_value('further.allow_multiple', default=False, data_type='boolean')">--- Please choose ---</option>
  <py:if test="priority">
    <option py:for="territory in territories" value="${territory[0]}" py:if="territory[0] in priority">${territory[1]}</option>
    <option value="" disabled="disabled">--------------------</option>
  </py:if>
  <option py:for="territory in territories" value="${territory[0]}" py:if="territory[0] not in priority">${territory[1]}</option>
</select>"""},
                     {'name': u'language',
                      'title': u'Language selection',
                      'dbschema': dumps([{'type': 'attr', 'attr': 'further.priority', 'default': '', 'group_order': 0},
                                         {'type': 'attr', 'attr': 'further.allow_multiple', 'default': 'no', 'group_order': 1}]),
                      'answer_validation': dumps({'type': 'unicode', 'params': {'allow_multiple': {'type': 'attr', 'attr': 'further.allow_multiple', 'default': False, 'data_type': 'boolean'}}}),
                      'backend': dumps([{'type': 'question-name'},
                                        {'type': 'question-title'},
                                        {'type': 'question-help'},
                                        {'type': 'question-required'},
                                        {'type': 'unicode', 'name': 'priority', 'title': 'Prioritise these countries', 'attr': 'further.priority', 'default': '', 'validator': {'not_empty': False, 'if_empty': ''}},
                                        {'type': 'select', 'name': 'multiple', 'title': 'Allow multiple selection', 'attr': 'further.allow_multiple', 'values': [('False', 'No'), ('True', 'Yes')], 'default': 'False', 'validator': {}}]),
                      'frontend': """<?python
    from babel import Locale
    locale = Locale('en')
    languages = locale.languages.items()
    languages.sort(key=lambda t:t[1])
?>
<select name="${name}" py:with="priority=[l.strip().lower() for l in q.attr_value('further.priority', default='').split(',') if l.strip()]" py:attrs="{'multiple': 'multiple' if q.attr_value('further.allow_multiple', default=False, data_type='boolean') else None}">
  <option value="" py:if="not q.attr_value('further.allow_multiple', default=False, data_type='boolean')">--- Please choose ---</option>
  <py:if test="priority">
    <option py:for="language in languages" value="${language[0]}" py:if="language[0] in priority">${language[1]}</option>
    <option value="" disabled="disabled">--------------------</option>
  </py:if>
  <option py:for="language in languages" value="${language[0]}" py:if="language[0] not in priority">${language[1]}</option>
</select>"""}]

def init_data(DBSession):
    with transaction.manager:
        user = User(u'admin', u'admin@example.com', u'Admin', u'adminPWD')
        group = Group(title='Site administrator')
        group.permissions.append(Permission(name='admin.users', title='Administer the users'))
        group.permissions.append(Permission(name='admin.groups', title='Administer the permission groups'))
        user.groups.append(group)
        group = Group(title='Developer')
        group.permissions.append(Permission(name='survey.new', title='Create new surveys'))
        user.groups.append(group)
        DBSession.add(user)
        group = Group(title='Content administrator')
        group.permissions.append(Permission(name='survey.view-all', title='View all surveys'))
        group.permissions.append(Permission(name='survey.edit-all', title='Edit all surveys'))
        group.permissions.append(Permission(name='survey.delete-all', title='Delete all surveys'))
        DBSession.add(group)
        q_type_group = QuestionTypeGroup(name='core', title='Core Questions', order=0)
        DBSession.add(q_type_group)
        for schema in DEFAULT_QUESTIONS:
            DBSession.add(QuestionType(name=schema['name'],
                                       title=schema['title'],
                                       dbschema=schema['dbschema'],
                                       answer_validation=schema['answer_validation'],
                                       backend=schema['backend'],
                                       frontend=schema['frontend'],
                                       q_type_group=q_type_group
                                       ))

def init_test_data(DBSession):
    def load_questions(qsheet, doc, DBSession):
        for item in doc:
            if item.tag == '{http://paths.sheffield.ac.uk/pyquest}questions':
                load_questions_from_xml(qsheet, item, DBSession, cleanup=False)
    with transaction.manager:
        user = DBSession.query(User).first()
        # SURVEY 1
        survey = Survey(title='A test survey', status='develop', styles='', scripts='')
        # PAGE 1
        source="""<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="text_entry" title="Text entry questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:question>
  <pq:type>text</pq:type>
  <pq:attribute name="text.text"><p>
    The first page demonstrates the basic question types</p>
</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>short_text</pq:type>
  <pq:name>single_text</pq:name>
  <pq:title>This is a (required) pq:short_text question</pq:title>
  <pq:help>Just a bit of help</pq:help>
  <pq:required>true</pq:required>
</pq:question>
<pq:question>
  <pq:type>long_text</pq:type>
  <pq:name>multi_text</pq:name>
  <pq:title>A pq:long_text question</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
</pq:question>
<pq:question>
  <pq:type>number</pq:type>
  <pq:name>number</pq:name>
  <pq:title>The pq:number question only allows numbers to be input</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
  <pq:attribute name="further.min">1</pq:attribute>
  <pq:attribute name="further.max">3</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>email</pq:type>
  <pq:name>email</pq:name>
  <pq:title>The pq:email question forces a valid e-mail address</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
</pq:question>
<pq:question>
  <pq:type>url</pq:type>
  <pq:name>url</pq:name>
  <pq:title>The pq:url question forces a http or https URL</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
</pq:question>
<pq:question>
  <pq:type>date</pq:type>
  <pq:name>date</pq:name>
  <pq:title>The pq:date question requires a valid date</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
</pq:question>
<pq:question>
  <pq:type>time</pq:type>
  <pq:name>time</pq:name>
  <pq:title>The pq:time question requires a valid time</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
</pq:question>
<pq:question>
  <pq:type>datetime</pq:type>
  <pq:name>datetime</pq:name>
  <pq:title>The pq:datetime question requires a valid date and time</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
</pq:question>
<pq:question>
  <pq:type>month</pq:type>
  <pq:name>month</pq:name>
  <pq:title>The pq:month question requires a month number between 1 and 12 or at least three letters of the English month name</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
</pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet1 = QSheet(name='text_entry', title='Text entry questions', styles='', scripts='')
        qsheet1.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet1.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet1.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet1.attributes.append(QSheetAttribute(key='qnumbers', value='no'))
        load_questions(qsheet1, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet1)
        # PAGE 2
        source = """<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="single_choice" title="Single choice questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:question>
  <pq:type>text</pq:type>
  <pq:attribute name="text.text"><p>
    The second page demonstrates the basic single choice questions.</p>
</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>single_choice</pq:type>
  <pq:name>single_choice_1</pq:name>
  <pq:title>Single choice</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute name="further.subtype">table</pq:attribute>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute name="further.allow_other">no</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>single_choice</pq:type>
  <pq:name>single_choice_2</pq:name>
  <pq:title>A vertical list single choice (with an optional answer)</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
  <pq:attribute name="further.subtype">list</pq:attribute>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute name="further.allow_other">single</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>single_choice</pq:type>
  <pq:name>single_choice_3</pq:name>
  <pq:title>A drop-down select single choice (required)</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
  <pq:attribute name="further.subtype">select</pq:attribute>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute name="further.allow_other">no</pq:attribute>
</pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet2 = QSheet(name='single_choice', title='Single choice questions', styles='', scripts='')
        qsheet2.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet2.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet2.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet2.attributes.append(QSheetAttribute(key='qnumbers', value='no'))
        load_questions(qsheet2, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet2)
        # PAGE 3
        source = """<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="multi_choice" title="Multi choice questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:question>
  <pq:type>text</pq:type>
  <pq:attribute name="text.text"><p>
    The third page demonstrates the basic multi choice questions.</p>
</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>multi_choice</pq:type>
  <pq:name>multi_choice_1</pq:name>
  <pq:title>A horizontal multi choice</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
  <pq:attribute name="further.subtype">table</pq:attribute>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute name="further.allow_other">no</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>multi_choice</pq:type>
  <pq:name>multi_choice_2</pq:name>
  <pq:title>A vertical list multi choice (with an optional answer)</pq:title>
  <pq:help></pq:help>
  <pq:required>false</pq:required>
  <pq:attribute name="further.subtype">list</pq:attribute>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute name="further.allow_other">single</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>multi_choice</pq:type>
  <pq:name>multi_choice_3</pq:name>
  <pq:title>A list select multi choice (required)</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute name="further.subtype">select</pq:attribute>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute name="further.allow_other">no</pq:attribute>
</pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet3 = QSheet(name='multi_choice', title='Multi choice questions', styles='', scripts='')
        qsheet3.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet3.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet3.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet3.attributes.append(QSheetAttribute(key='qnumbers', value='no'))
        load_questions(qsheet3, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet3)
        # PAGE 4
        source = """<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="grids" title="Grid-based questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:question>
  <pq:type>text</pq:type>
  <pq:attribute name="text.text"><p>
    The fourth page demonstrates the grid-based single and multi choice questions.</p>
</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>single_choice_grid</pq:type>
  <pq:name>grid_1</pq:name>
  <pq:title>A grid of single choice questions</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute_group name="subquestion">
    <pq:attribute>
      <pq:value name="name">q1</pq:value>
      <pq:value name="label">Question 1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="name">q2</pq:value>
      <pq:value name="label">Question 2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="name">q3</pq:value>
      <pq:value name="label">Question 3</pq:value>
    </pq:attribute>
  </pq:attribute_group>
</pq:question>
<pq:question>
  <pq:type>multi_choice_grid</pq:type>
  <pq:name>grid_2</pq:name>
  <pq:title>A grid of multi choice questions (required)</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute_group name="subquestion">
    <pq:attribute>
      <pq:value name="name">q1</pq:value>
      <pq:value name="label">Question 1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="name">q2</pq:value>
      <pq:value name="label">Question 2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="name">q3</pq:value>
      <pq:value name="label">Question 3</pq:value>
    </pq:attribute>
  </pq:attribute_group>
</pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet4 = QSheet(name='grids', title='Grid-based questions', styles='', scripts='')
        qsheet4.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet4.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet4.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet4.attributes.append(QSheetAttribute(key='qnumbers', value='no'))
        load_questions(qsheet4, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet4)
        # PAGE 5
        source ="""<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="other" title="Other questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:question>
  <pq:type>text</pq:type>
  <pq:attribute name="text.text"><p>
    The fifth page demonstrates the other questions.</p>
</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>confirm</pq:type>
  <pq:name>confirmation_1</pq:name>
  <pq:title>A checkbox to confirm a value</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute name="further.value">yes</pq:attribute>
  <pq:attribute name="further.label">Label to show next to the checkbox</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>ranking</pq:type>
  <pq:name>ranking_1</pq:name>
  <pq:title>Ranking of multiple elements (required)</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">dog</pq:value>
      <pq:value name="label">Dog</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">cat</pq:value>
      <pq:value name="label">Cat</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">mouse</pq:value>
      <pq:value name="label">Mouse</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">bird</pq:value>
      <pq:value name="label">Bird</pq:value>
    </pq:attribute>
  </pq:attribute_group>
</pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet5 = QSheet(name='other', title='Other questions', styles='', scripts='')
        qsheet5.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet5.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet5.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet5.attributes.append(QSheetAttribute(key='qnumbers', value='no'))
        load_questions(qsheet5, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet5)
        survey.start = qsheet1
        QSheetTransition(source=qsheet1, target=qsheet2)
        QSheetTransition(source=qsheet2, target=qsheet3)
        QSheetTransition(source=qsheet3, target=qsheet4)
        QSheetTransition(source=qsheet4, target=qsheet5)
        user.surveys.append(survey)
        DBSession.add(survey)
        
        # SURVEY 2
        survey = Survey(title='A test sampling survey', status='develop', styles='', scripts='')
        # PAGE 1
        source="""<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="consent" title="Welcome">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:question>
  <pq:type>confirm</pq:type>
  <pq:name>consent</pq:name>
  <pq:title>Informed consent</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute name="further.value">yes</pq:attribute>
  <pq:attribute name="further.label">I know what I am letting myself in for</pq:attribute>
</pq:question>
<pq:question>
  <pq:type>text</pq:type>
  <pq:attribute name="text.text"><p>
    Welcome to this survey.</p>
<p>
    You will be shown a number of items with questions.</p>
</pq:attribute>
</pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet1 = QSheet(name='welcome', title='Welcome', styles='', scripts='')
        qsheet1.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet1.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet1.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet1.attributes.append(QSheetAttribute(key='qnumbers', value='no'))
        load_questions(qsheet1, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet1)
        """
        question = Question(name='', title='', required=False, help='', order=0)
        qa_group = QuestionAttributeGroup(key='text', label='Free text')
        qa_group.attributes.append(QuestionAttribute(key='text', label='Free text', value='<p>Welcome to this survey.</p><p>You will be shown a number of items with questions.</p>', order=0))
        question.attributes.append(qa_group)
        qsheet1.questions.append(question)
        question = Question(type='confirm', name='consent', title='Informed consent', required=True, help='', order=1)
        qa_group = QuestionAttributeGroup(key='further', label='Answer', order=0)
        qa_group.attributes.append(QuestionAttribute(key='value', label='Value', value='true', order=0))
        qa_group.attributes.append(QuestionAttribute(key='label', label='Label', value='I know what I am letting myself in for', order=1))
        question.attributes.append(qa_group)
        qsheet1.questions.append(question)
        """
        # PAGE 2
        source="""<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="data" title="Rate these pages">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:question>
  <pq:type>text</pq:type>
  <pq:attribute name="text.text"><p>How well does this URL match the title?</p><p>URL: ${url}</p><p>Title: ${title}</p></pq:attribute>
</pq:question>
<pq:question>
  <pq:type>single_choice</pq:type>
  <pq:name>rating</pq:name>
  <pq:title>Rate how well the title matches the url</pq:title>
  <pq:help></pq:help>
  <pq:required>true</pq:required>
  <pq:attribute name="further.subtype">table</pq:attribute>
  <pq:attribute name="further.before_label">Not good</pq:attribute>
  <pq:attribute name="further.after_label">Very good</pq:attribute>
  <pq:attribute_group name="answer">
    <pq:attribute>
      <pq:value name="value">0</pq:value>
      <pq:value name="label">1</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">1</pq:value>
      <pq:value name="label">2</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">2</pq:value>
      <pq:value name="label">3</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">3</pq:value>
      <pq:value name="label">4</pq:value>
    </pq:attribute>
    <pq:attribute>
      <pq:value name="value">4</pq:value>
      <pq:value name="label">5</pq:value>
    </pq:attribute>
  </pq:attribute_group>
  <pq:attribute name="further.allow_other">no</pq:attribute>
</pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet2 = QSheet(name='data', title='Rate these pages', styles='', scripts='')
        qsheet2.attributes.append(QSheetAttribute(key='repeat', value='repeat'))
        qsheet2.attributes.append(QSheetAttribute(key='data-items', value='4'))
        qsheet2.attributes.append(QSheetAttribute(key='control-items', value='1'))
        qsheet2.attributes.append(QSheetAttribute(key='qnumbers', value='no'))
        load_questions(qsheet2, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet2)
        survey.start = qsheet1
        QSheetTransition(source=qsheet1, target=qsheet2)
        question = DBSession.query(Question).filter(Question.qsheet_id==qsheet2.id).filter(Question.name=='rating').first()
        """
        question = Question(type='text', name='', title='', required=False, help='', order=0)
        qa_group = QuestionAttributeGroup(key='text', label='Free text')
        qa_group.attributes.append(QuestionAttribute(key='text', label='Free text', value='<p>How well does this URL match the title?</p><p>URL: ${url}</p><p>Title: ${title}</p>', order=0))
        question.attributes.append(qa_group)
        qsheet2.questions.append(question)
        question = Question(type='rating', name='match', title='How well does the URL match the title?', required=True, help='', order=1)
        qa_group = QuestionAttributeGroup(key='answer', label='Answer', order=0)
        qa_group.attributes.append(QuestionAttribute(key='value', label='Value', value='0', order=0))
        qa_group.attributes.append(QuestionAttribute(key='label', label='Label', value='1 - Not at all', order=1))
        question.attributes.append(qa_group)
        qa_group = QuestionAttributeGroup(key='answer', label='Answer', order=1)
        qa_group.attributes.append(QuestionAttribute(key='value', label='Value', value='1', order=0))
        qa_group.attributes.append(QuestionAttribute(key='label', label='Label', value='2', order=1))
        question.attributes.append(qa_group)
        qa_group = QuestionAttributeGroup(key='answer', label='Answer', order=2)
        qa_group.attributes.append(QuestionAttribute(key='value', label='Value', value='2', order=0))
        qa_group.attributes.append(QuestionAttribute(key='label', label='Label', value='3', order=1))
        question.attributes.append(qa_group)
        qa_group = QuestionAttributeGroup(key='answer', label='Answer', order=3)
        qa_group.attributes.append(QuestionAttribute(key='value', label='Value', value='3', order=0))
        qa_group.attributes.append(QuestionAttribute(key='label', label='Label', value='4', order=1))
        question.attributes.append(qa_group)
        qa_group = QuestionAttributeGroup(key='answer', label='Answer', order=4)
        qa_group.attributes.append(QuestionAttribute(key='value', label='Value', value='4', order=0))
        qa_group.attributes.append(QuestionAttribute(key='label', label='Label', value='5 - Perfectly', order=1))
        question.attributes.append(qa_group)
        qsheet2.questions.append(question)
        """
        # DATA ITEMS
        data_item = DataItem(order=1)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the first item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/1.html'))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=2)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the second item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/2.html'))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=3, control=True)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the third item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/3.html'))
        data_item.control_answers.append(DataItemControlAnswer(answer='0', question=question))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=4)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the fourth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/4.html'))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=5)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the fifth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/5.html'))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=6)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the sixth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/6.html'))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=7, control=True)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the seventh item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/7.html'))
        data_item.control_answers.append(DataItemControlAnswer(answer='4', question=question))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=8)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the eighth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/8.html'))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=9)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the ninth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/9.html'))
        qsheet2.data_items.append(data_item)
        data_item = DataItem(order=10)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the tenth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/10.html'))
        qsheet2.data_items.append(data_item)
        user.surveys.append(survey)
        DBSession.add(survey)
        
