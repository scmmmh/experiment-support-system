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
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config
from lxml import etree

from pyquest.models import (DBSession, Base, Survey, QSheet, DataItem,
                            DataItemAttribute, User, Group, Permission,
                            Question, QuestionAttributeGroup, QuestionAttribute,
                            QSheetTransition, QSheetAttribute,
                            DataItemControlAnswer)
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
    Base.metadata.create_all(engine)
    init_data(DBSession)
    alembic_cfg = Config(config_uri)
    command.stamp(alembic_cfg, "head")
    if len(argv) == 2 or argv[2] != '--no-test-data':
        init_test_data(DBSession)

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
    <pq:static_text><p>The first page demonstrates the basic question types</p></pq:static_text>
<pq:short_text name="short_text" title="This is a (required) pq:short_text question" help="Just a bit of help"/>
<pq:long_text name="long_text" title="A pq:long_text question" help=""/>
<pq:number name="number" title="The pq:number question only allows numbers to be input" help="" min="" max=""/>
<pq:email name="email" title="The pq:email question forces a valid e-mail address" help=""/>
<pq:url name="url" title="The pq:url question forces a http or https URL" help=""/>
<pq:date name="date" title="The pq:date question requires a valid date" help=""/>
<pq:time name="time" title="The pq:time question requires a valid time" help=""/>
<pq:datetime name="datetime" title="The pq:datetime question requires a valid date and time" help=""/>
<pq:month name="month" title="The pq:month question requires a month number between 1 and 12 or at least three letters of the English month name" help=""/>
  </pq:questions>
</pq:qsheet>
        """
        qsheet1 = QSheet(name='text_entry', title='Text entry questions', styles='', scripts='')
        qsheet1.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet1.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet1.attributes.append(QSheetAttribute(key='control-items', value='0'))
        load_questions(qsheet1, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet1)
        # PAGE 2
        source = """<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="single_choice" title="Single choice questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:static_text><p>
    The second page demonstrates the basic single choice questions.</p>
</pq:static_text>
<pq:single_choice name="single_choice_1" title="A horizontal single choice" help="" display="table" allow_other="no" before_label="Very good" after_label="Very bad">
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:single_choice>
<pq:single_choice name="single_choice_2" title="A vertical list single choice (with an optional answer)" help="" display="list" allow_other="single" before_label="First" after_label="Last">
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:single_choice>
<pq:single_choice name="single_choice_3" title="A drop-down select single choice (required)" help="" display="select" allow_other="no" before_label="" after_label="">
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:single_choice>
  </pq:questions>
</pq:qsheet>
        """
        qsheet2 = QSheet(name='single_choice', title='Single choice questions', styles='', scripts='')
        qsheet1.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet1.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet1.attributes.append(QSheetAttribute(key='control-items', value='0'))
        load_questions(qsheet2, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet2)
        # PAGE 3
        source = """<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="multi_choice" title="Multi choice questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:static_text><p>
    The third page demonstrates the basic multi choice questions.</p>
</pq:static_text>
<pq:multi_choice name="multi_choice_1" title="A horizontal multi choice" help="" display="table" allow_other="no" before_label="Very good" after_label="Very bad">
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:multi_choice>
<pq:multi_choice name="multi_choice_2" title="A vertical list multi choice (with an optional answer)" help="" display="list" allow_other="single" before_label="First" after_label="Last">
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:multi_choice>
<pq:multi_choice name="multi_choice_3" title="A list select multi choice (required)" help="" display="select" allow_other="no" before_label="" after_label="">
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:multi_choice>
  </pq:questions>
</pq:qsheet>
        """
        qsheet3 = QSheet(name='multi_choice', title='Multi choice questions', styles='', scripts='')
        qsheet3.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet3.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet3.attributes.append(QSheetAttribute(key='control-items', value='0'))
        load_questions(qsheet3, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet3)
        # PAGE 4
        source = """<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="grids" title="Grid-based questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:static_text><p>
    The fourth page demonstrates the grid-based single and multi choice questions.</p>
</pq:static_text>
<pq:single_choice_grid name="grid_1" title="A grid of single choice questions" help="" before_label="Minimum" after_label="Maximum">
  <pq:sub_question name="q1" label="Question 1"/>
  <pq:sub_question name="q2" label="Question 2"/>
  <pq:sub_question name="q3" label="Question 3"/>
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:single_choice_grid>
<pq:multi_choice_grid name="grid_2" title="A grid of multi choice questions (required)" help="" before_label="Start" after_label="End">
  <pq:sub_question name="q1" label="Question 1"/>
  <pq:sub_question name="q2" label="Question 2"/>
  <pq:sub_question name="q3" label="Question 3"/>
  <pq:answer value="0" label="1"/>
  <pq:answer value="1" label="2"/>
  <pq:answer value="2" label="3"/>
  <pq:answer value="3" label="4"/>
  <pq:answer value="4" label="5"/>
</pq:multi_choice_grid>
  </pq:questions>
</pq:qsheet>
        """
        qsheet4 = QSheet(name='grids', title='Grid-based questions', styles='', scripts='')
        qsheet4.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet4.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet4.attributes.append(QSheetAttribute(key='control-items', value='0'))
        load_questions(qsheet4, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet4)
        # PAGE 5
        source ="""<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="other" title="Other questions">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
    <pq:static_text><p>
    The fifth page demonstrates the other questions.</p>
</pq:static_text>
<pq:confirm name="confirmation_1" title="A checkbox to confirm a value" help="" value="yes" label="Label to show next to the checkbox"/>
<pq:ranking name="ranking_1" title="Ranking of multiple elements (required)" help="" before_label="Best" after_label="Worst">
  <pq:answer value="dog" label="Dog"/>
  <pq:answer value="cat" label="Cat"/>
  <pq:answer value="mouse" label="Mouse"/>
  <pq:answer value="bird" label="Bird"/>
</pq:ranking>
  </pq:questions>
</pq:qsheet>
        """
        qsheet5 = QSheet(name='other', title='Other questions', styles='', scripts='')
        qsheet5.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet5.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet5.attributes.append(QSheetAttribute(key='control-items', value='0'))
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
        qsheet1 = QSheet(name='welcome', title='Welcome', styles='', scripts='')
        qsheet1.attributes.append(QSheetAttribute(key='repeat', value='single'))
        qsheet1.attributes.append(QSheetAttribute(key='data-items', value='0'))
        qsheet1.attributes.append(QSheetAttribute(key='control-items', value='0'))
        question = Question(type='text', name='', title='', required=False, help='', order=0)
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
        survey.qsheets.append(qsheet1)
        # PAGE 2
        qsheet2 = QSheet(name='data', title='Rate these pages', styles='', scripts='')
        qsheet2.attributes.append(QSheetAttribute(key='repeat', value='repeat'))
        qsheet2.attributes.append(QSheetAttribute(key='data-items', value='4'))
        qsheet2.attributes.append(QSheetAttribute(key='control-items', value='1'))
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
        survey.qsheets.append(qsheet2)
        survey.start = qsheet1
        QSheetTransition(source=qsheet1, target=qsheet2)
        # DATA ITEMS
        data_item = DataItem(order=1)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the first item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/1.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=2)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the second item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/2.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=3, control=True)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the third item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/3.html'))
        data_item.control_answers.append(DataItemControlAnswer(answer='0', question=question))
        survey.data_items.append(data_item)
        data_item = DataItem(order=4)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the fourth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/4.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=5)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the fifth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/5.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=6)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the sixth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/6.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=7, control=True)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the seventh item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/7.html'))
        data_item.control_answers.append(DataItemControlAnswer(answer='4', question=question))
        survey.data_items.append(data_item)
        data_item = DataItem(order=8)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the eighth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/8.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=9)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the ninth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/9.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=10)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the tenth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/10.html'))
        survey.data_items.append(data_item)
        user.surveys.append(survey)
        DBSession.add(survey)
        