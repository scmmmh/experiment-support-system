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
from csv import DictReader
from json import dumps
from lxml import etree
from pkg_resources import resource_stream
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

from pyquest.models import (DBSession, Base, Survey, QSheet, DataItem,
                            DataItemAttribute, User, Group, Permission,
                            Question, QSheetTransition, QSheetAttribute,
                            DataItemControlAnswer, DataSet, DataSetAttributeKey)
from pyquest.validation import XmlValidator
from pyquest.views.admin.question_types import load_q_types_from_xml
from pyquest.views.backend.qsheet import load_questions_from_xml
from pyquest.views.backend.survey import load_survey_from_xml

def init(subparsers):
    parser = subparsers.add_parser('initialise-database', help='Initialise the database')
    parser.add_argument('configuration', help='PyQuestionnaire configuration file')
    parser.add_argument('--drop-existing', action='store_true', default=False, help='Drop any existing tables')
    parser.set_defaults(func=initialise_database)
    parser = subparsers.add_parser('load-test-data', help='Load the test data')
    parser.add_argument('configuration', help='PyQuestionnaire configuration file')
    parser.set_defaults(func=load_test_data)

def initialise_database(args):
    settings = get_appsettings(args.configuration)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    if args.drop_existing:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    dbsession = DBSession()
    with transaction.manager:
        user = User(u'admin', u'admin@example.com', u'Admin', u'password')
        group = Group(title='Site administrator')
        group.permissions.append(Permission(name='admin.users', title='Administer the users'))
        group.permissions.append(Permission(name='admin.groups', title='Administer the permission groups'))
        group.permissions.append(Permission(name='admin.question_types', title='Administer the question types'))
        user.groups.append(group)
        group = Group(title='Developer')
        group.permissions.append(Permission(name='survey.new', title='Create new surveys'))
        user.groups.append(group)
        dbsession.add(user)
        group = Group(title='Content administrator')
        group.permissions.append(Permission(name='survey.view-all', title='View all surveys'))
        group.permissions.append(Permission(name='survey.edit-all', title='Edit all surveys'))
        group.permissions.append(Permission(name='survey.delete-all', title='Delete all surveys'))
        dbsession.add(group)
        element = XmlValidator().to_python(resource_stream('pyquest', 'scripts/templates/default_question_types.xml').read())
        dbsession.add(load_q_types_from_xml(dbsession, element, 0))
    alembic_cfg = Config(args.configuration)
    command.stamp(alembic_cfg, "head")

def load_test_data(args):
    settings = get_appsettings(args.configuration)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    def load_questions(qsheet, doc, DBSession):
        for item in doc:
            if item.tag == '{http://paths.sheffield.ac.uk/pyquest}questions':
                load_questions_from_xml(qsheet, item, DBSession, cleanup=False)
    dbsession = DBSession()
    with transaction.manager:
        user = dbsession.query(User).first()
        
        # Sample Survey 1
        element = XmlValidator().to_python(resource_stream('pyquest', 'scripts/templates/sample_survey_1.xml').read())
        dbsession.add(load_survey_from_xml(user, dbsession, element))
        
        # Sample Survey 2
        element = XmlValidator().to_python(resource_stream('pyquest', 'scripts/templates/sample_survey_2.xml').read())
        survey = load_survey_from_xml(user, dbsession, element)
        dbsession.add(survey)
        data_set = DataSet(name='test_samples', owned_by=user.id)
        data_set.survey = survey
        reader = DictReader(resource_stream('pyquest', 'scripts/templates/sample_survey_2.csv'))
        keys = {}
        for idx, column in enumerate(reader.fieldnames):
            attr_key = DataSetAttributeKey(key=column, order=idx)
            data_set.attribute_keys.append(attr_key)
            keys[column] = attr_key
        for line in reader:
            data_item = DataItem(data_set=data_set)
            for column, value in line.items():
                data_item.attributes.append(DataItemAttribute(key=keys[column], value=value))
        for qsheet in survey.qsheets:
            if qsheet.name == 'data':
                qsheet.data_set = data_set
        '''
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
        qsheet1.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
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
        qsheet2.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
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
        qsheet3.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
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
        qsheet4.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
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
        qsheet5.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
        load_questions(qsheet5, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet5)
        survey.start = qsheet1
        QSheetTransition(source=qsheet1, target=qsheet2)
        QSheetTransition(source=qsheet2, target=qsheet3)
        QSheetTransition(source=qsheet3, target=qsheet4)
        QSheetTransition(source=qsheet4, target=qsheet5)
        user.surveys.append(survey)
        dbsession.add(survey)
        
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
        qsheet1.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
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
        qsheet2.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
        load_questions(qsheet2, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet2)
        survey.start = qsheet1
        QSheetTransition(source=qsheet1, target=qsheet2)
        question = dbsession.query(Question).filter(Question.qsheet_id==qsheet2.id).filter(Question.name=='rating').first()
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
        dataset = DataSet(name="TestDataSet")
        key_one = DataSetAttributeKey(key='title', order=1)
        dataset.attribute_keys.append(key_one)
        key_two = DataSetAttributeKey(key='url', order=2)
        dataset.attribute_keys.append(key_two)

        data_item = DataItem(order=1)
        dia = DataItemAttribute(value='This is the first item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/1.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        data_item = DataItem(order=2)
        dia = DataItemAttribute(value='This is the second item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/2.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        data_item = DataItem(order=3, control=True)
        dia = DataItemAttribute(value='This is the third item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/3.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        data_item.control_answers.append(DataItemControlAnswer(answer='0', question=question))
        dataset.items.append(data_item)

        data_item = DataItem(order=4)
        dia = DataItemAttribute(value='This is the fourth item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/4.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        data_item = DataItem(order=5)
        dia = DataItemAttribute(value='This is the fifth item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/5.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        data_item = DataItem(order=6)
        dia = DataItemAttribute(value='This is the sixth item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/6.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        data_item = DataItem(order=7, control=True)
        dia = DataItemAttribute(value='This is the seventh item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/7.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        data_item.control_answers.append(DataItemControlAnswer(answer='4', question=question))
        dataset.items.append(data_item)

        data_item = DataItem(order=8)
        dia = DataItemAttribute(value='This is the eighth item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/8.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        data_item = DataItem(order=9)
        dia = DataItemAttribute(value='This is the ninth item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/9.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        data_item = DataItem(order=10)
        dia = DataItemAttribute(value='This is the tenth item')
        data_item.attributes.append(dia)
        key_one.values.append(dia)
        dia = DataItemAttribute(value='http://www.example.com/10.html')
        data_item.attributes.append(dia)
        key_two.values.append(dia)
        dataset.items.append(data_item)

        dataset.qsheets.append(qsheet2)
        survey.data_sets.append(dataset)
        user.data_sets.append(dataset)
        user.surveys.append(survey)
        dbsession.add(survey)
        '''

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

        # SURVEY 3
        survey = Survey(title='A very simple survey', status='develop', styles='', scripts='')
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
        qsheet1.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
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
        survey.start = qsheet1
        notification = Notification(ntype='interval', value=60, recipient='paul@paulserver.paulsnetwork')
        survey.notifications.append(notification)
        notification = Notification(ntype='pcount', value=1, recipient='paul@paulserver.paulsnetwork')
        survey.notifications.append(notification)
        user.surveys.append(survey)
        DBSession.add(survey)
