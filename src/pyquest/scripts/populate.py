# -*- coding: utf-8 -*-

try:
    import cPickle as pickle
except:
    import pickle
import os
import sys
import transaction

from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

from pyquest.models import (DBSession, Base, Survey, QSheet, DataItem,
                            DataItemAttribute, User, Group, Permission)
from pyquest import validation
from pyquest.views.backend import survey as survey_backend

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
    if len(argv) == 2 or argv[2] != '--no-data':
        init_test_data(DBSession)

def init_data(DBSession):
    with transaction.manager:
        user = User(u'mhall', u'm.mhall@sheffield.ac.uk', u'Archchancellor', u'test')
        group = Group(name='administrator', title='Administrator')
        group.permissions.append(Permission(name='admin.configuration'))
        group.permissions.append(Permission(name='admin.users'))
        user.groups.append(group)
        DBSession.add(user)

def init_test_data(DBSession):
    with transaction.manager:
        user = DBSession.query(User).first()
        survey = Survey(title='A test survey', content="""<pq:single qsid="1"/>
<pq:repeat qsid="2">
  <pq:data_items count="5"/>
</pq:repeat>
<pq:finish qsid="3"/>""", summary='A simple test survey', status='develop')
        survey.schema = pickle.dumps(survey_backend.create_schema('<pq:survey xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:survey>' % survey.content))
        survey.owner = user
        qsheet = QSheet(name='consent', title='Welcome', content="""<p>Thank you for participating
in this survey, your time is much appreciated.</p>
<p>Your data will be stored annonymously and in full compliance with the Data Protection Act.
Your data will only be used for reasearch purposes and will not be shared with anyone outside
the research group.</p>
<pq:confirm name="informed_consent" title="Please confirm that you have understood this" label="I confirm" required="true"/>""")
        qsheet.schema = pickle.dumps(validation.qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % qsheet.content))
        survey.qsheets.append(qsheet)
        qsheet = QSheet(name='rating', title='Rate this URL', content="""<p>Please rate the content
of the following url, based on its title</p>
<dl>
  <dt>Title</dt>
  <dd>${title}</dd>
  <dt>URL</dt>
  <dd>${url}</dd>
</dl>
<pq:rating name="match" title="How well does the title match the URL?" required="true">
  <pq:option title="Not at all" value="1"/>
  <pq:option value="2"/>
  <pq:option value="3"/>
  <pq:option value="4"/>
  <pq:option title="Perfectly" value="5"/>
</pq:rating>
""")
        qsheet.schema = pickle.dumps(validation.qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % qsheet.content))
        survey.qsheets.append(qsheet)
        qsheet = QSheet(name='finish', title='Thank you very much', content="""<p>Thank you very much
for completing our survey. Your time and effort have been a great help.</p>""")
        qsheet.schema = pickle.dumps(validation.qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % qsheet.content))
        survey.qsheets.append(qsheet)
        data_item = DataItem(order=1)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the first item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/1.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=2)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the second item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/2.html'))
        survey.data_items.append(data_item)
        data_item = DataItem(order=3)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the third item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/3.html'))
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
        data_item = DataItem(order=7)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the seventh item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/7.html'))
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
        DBSession.add(survey)
        survey = Survey(title='Tests all question types', content='''<pq:single qsid="4"/>
<pq:single qsid="5"/>
<pq:single qsid="6"/>
<pq:single qsid="7"/>''', status='develop')
        survey.schema = pickle.dumps(survey_backend.create_schema('<pq:survey xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:survey>' % survey.content))
        qsheet = QSheet(name='p1', title='Page 1', content='''<p>This is the first page, demonstrating the different input field types.</p>
<pq:short_text name="short_text" title="This is a (required) pq:short_text question" required="true"/>
<pq:long_text name="long_text" title="A pq:long_text question"/>
<pq:number name="number" title="The pq:number question only allows numbers to be input" min="2" max="10" step="2"/>
<pq:email name="email" title="The pq:email question forces a valid e-mail address"/>
<pq:url name="url" title="The pq:url question forces a http or https URL"/>
<pq:date name="date" title="The pq:date question requires a valid date"/>
<pq:time name="time" title="The pq:time question requires a valid time"/>
<pq:datetime name="datetime" title="The pq:datetime question requires a valid date and time"/>
<pq:month name="month" title="The pq:month question requires a month number between 1 and 12 or at least three letters of the English month name"/>
''')
        qsheet.schema = pickle.dumps(validation.qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % qsheet.content))
        survey.qsheets.append(qsheet)
        survey.owner = user
        qsheet = QSheet(name='p2', title='Page 2', content='''<p>This page demonstrates the available single-choice questions</p>
<pq:rating name="rating_1" title="The pq:rating question provides a choice of answers" min_value="1" min_title="First" max_value="5" max_title="Last"/>
<pq:rating name="rating_2" min_value="1" min_title="First" max_value="5" max_title="Last" hide_extra_labels="true"/>
<pq:rating name="rating_3" title="The pq:option element is used to define the choices">
  <pq:option value="1" title="First"/>
  <pq:option value="2"/>
  <pq:option value="3" title="Middle"/>
  <pq:option value="4"/>
  <pq:option value="5" title="Last"/>
</pq:rating>
<pq:rating_group name="rating_group" title="The pq:rating_group creates a grid of questions and answers">
  <pq:option value="1" title="First"/>
  <pq:option value="2"/>
  <pq:option value="3" title="Middle"/>
  <pq:option value="4"/>
  <pq:option value="5" title="Last"/>
  <pq:rating name="question_1" title="Question 1"/>
  <pq:rating name="question_2" title="Question 2"/>
  <pq:rating name="question_3" title="Question 3"/>
</pq:rating_group>
<pq:listchoice name="rating_4" title="The pq:listchoice displays the options as a list">
  <pq:option value="1" title="A"/>
  <pq:option value="2" title="B"/>
  <pq:option value="3" title="C"/>
  <pq:option value="4" title="D"/>
  <pq:option value="5" title="E"/>
</pq:listchoice>
<pq:selectchoice name="rating_5" title="The pq:selectchoice displays the options as a select box">
  <pq:option value="1" title="A"/>
  <pq:option value="2" title="B"/>
  <pq:option value="3" title="C"/>
  <pq:option value="4" title="D"/>
  <pq:option value="5" title="E"/>
</pq:selectchoice>
''')
        qsheet.schema = pickle.dumps(validation.qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % qsheet.content))
        survey.qsheets.append(qsheet)
        survey.owner = user
        qsheet = QSheet(name='p3', title='Page 3', content='''<p>This page demonstrates the multi-choice questions.</p>
<pq:multichoice name="multichoice" title="The pq:multichoice question allows multiple answers">
  <pq:option value="1" title="A"/>
  <pq:option value="2" title="B"/>
  <pq:option value="3" title="C"/>
  <pq:option value="4" title="D"/>
  <pq:option value="5" title="E"/>
</pq:multichoice>
<pq:multichoice_group name="multichoice_group" title="The pq:multichoice_group question allows multiple questions with the same possible answers to be grouped">
  <pq:option value="1" title="A"/>
  <pq:option value="2" title="B"/>
  <pq:option value="3" title="C"/>
  <pq:option value="4" title="D"/>
  <pq:option value="5" title="E"/>
  <pq:multichoice name="q1" title="Question 1"/>
  <pq:multichoice name="q2" title="Question 2"/>
  <pq:multichoice name="q3" title="Question 3"/>
</pq:multichoice_group>
''')
        qsheet.schema = pickle.dumps(validation.qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % qsheet.content))
        survey.qsheets.append(qsheet)
        survey.owner = user
        qsheet = QSheet(name='p4', title='Page 4', content='''<p>This page demonstrates the remaining question types</p>
<pq:confirm name="confirm" title="The pq:confirm question gets a yes/no decision" required="true"/>
<pq:ranking name="ranking" title="The pq:ranking question gets a ranking of pq:options">
  <pq:option value="cat" title="Cat"/>
  <pq:option value="dog" title="Dog"/>
  <pq:option value="mouse" title="Mouse"/>
  <pq:option value="horse" title="Horse"/>
  <pq:option value="elephant" title="Elephant"/>
</pq:ranking>''')
        qsheet.schema = pickle.dumps(validation.qsheet_to_schema('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % qsheet.content))
        survey.qsheets.append(qsheet)
        survey.owner = user
        DBSession.add(survey)
        user = User(u'mahall', u'm.mhall@sheffield.ac.uk', u'Mark')
        DBSession.add(user)
        survey = Survey(title='Auth test', status='develop')
        survey.owner = user
        qsheet = QSheet(title='A sheet', content='')
        survey.qsheets.append(qsheet)
        DBSession.add(survey)
