# -*- coding: utf-8 -*-

import transaction

from alembic import config, command
from csv import DictReader
from lxml import etree
from pkg_resources import resource_stream
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

from pyquest.models import (DBSession, Base, Survey, QSheet, DataItem,
                            DataItemAttribute, User, Group, Permission,
                            QSheetAttribute, QSheetTransition,
                            DataSet, DataSetAttributeKey, Notification, PermutationSet)
from pyquest.validation import XmlValidator
from pyquest.views.admin.question_types import load_q_types_from_xml
from pyquest.views.backend.qsheet import load_questions_from_xml
from pyquest.views.backend.survey import load_survey_from_xml
from pyquest import taskperms

def init(subparsers):
    parser = subparsers.add_parser('initialise-database', help='Initialise the database')
    parser.add_argument('configuration', help='PyQuestionnaire configuration file')
    parser.add_argument('--drop-existing', action='store_true', default=False, help='Drop any existing tables')
    parser.set_defaults(func=initialise_database)
    parser = subparsers.add_parser('load-sample-data', help='Loads the sample data')
    parser.add_argument('configuration', help='PyQuestionnaire configuration file')
    parser.set_defaults(func=load_test_data)

def initialise_database(args):
    settings = get_appsettings(args.configuration)
    setup_logging(args.configuration)
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
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'pyquest:migrations')
    command.stamp(alembic_config, "head")

def load_test_data(args):
    settings = get_appsettings(args.configuration)
    setup_logging(args.configuration)
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
        survey = load_survey_from_xml(user, dbsession, element)
        dbsession.add(survey)
        notification = Notification(ntype='interval', value=1, recipient=user.email)
        survey.notifications.append(notification)
        
        # Sample Survey 2
        element = XmlValidator().to_python(resource_stream('pyquest', 'scripts/templates/sample_survey_2.xml').read())
        survey = load_survey_from_xml(user, dbsession, element)
        dbsession.add(survey)
        data_set = DataSet(name='test_samples', owned_by=user.id)
        data_set.survey = survey
        reader = DictReader(resource_stream('pyquest', 'scripts/templates/sample_survey_2.csv'))
        keys = {}
        for idx, column in enumerate(reader.fieldnames):
            if column != 'control_':
                attr_key = DataSetAttributeKey(key=column, order=idx)
                data_set.attribute_keys.append(attr_key)
                keys[column] = attr_key
        for line in reader:
            data_item = DataItem(data_set=data_set)
            for column, value in line.items():
                if column == 'control_':
                    if value.lower() == 'true' or value.lower() == 't' or value.lower() == '1':
                        data_item.control = True
                    else:
                        data_item.control = False
                else:
                    data_item.attributes.append(DataItemAttribute(key=keys[column], value=value))
        for qsheet in survey.qsheets:
            if qsheet.name == 'data':
                qsheet.data_set = data_set
        notification = Notification(ntype='pcount', value=10, recipient=user.email)
        survey.notifications.append(notification)

        # SURVEY 4
        survey = Survey(title='Multi-task test survey', status='develop', styles='', scripts='')
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
        source="""<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="consent" title="Welcome">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
     <pq:question>
     <pq:type>confirm</pq:type>
     <pq:name>PermDone</pq:name>
     <pq:title>Participant ${pid_} imagine an iframe containing permutation ${perm} then tick the box</pq:title>
     <pq:help></pq:help>
     <pq:required>true</pq:required>
     <pq:attribute name="further.value">done</pq:attribute>
     <pq:attribute name="further.label">Imagined</pq:attribute>
     </pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet2 = QSheet(name='task_interface_page', title='Where the tasks are...', styles='', scripts='')
        qsheet2.attributes.append(QSheetAttribute(key='repeat', value='repeat'))
        qsheet2.attributes.append(QSheetAttribute(key='data-items', value='1'))
        qsheet2.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet2.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
        qsheet2.attributes.append(QSheetAttribute(key='task-count', value='2'))
        qsheet2.attributes.append(QSheetAttribute(key='interface-count', value='2'))
        load_questions(qsheet2, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet2)
        tasksds = DataSet(name="two_tasks", owned_by=user.id, survey_id=survey.id)
        tasksds.attribute_keys.append(DataSetAttributeKey(key='name', order=0))
        survey.data_sets.append(tasksds)
        dbsession.flush()
        taskitem = DataItem(order=0)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="A", key_id=ak.id))
        tasksds.items.append(taskitem)
        taskitem = DataItem(order=1)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="B", key_id=ak.id))
        tasksds.items.append(taskitem)

        interfacesds = DataSet(name="two_interfaces", owned_by=user.id, survey_id=survey.id)
        interfacesds.attribute_keys.append(DataSetAttributeKey(key='name', order=0))
        survey.data_sets.append(interfacesds)
        dbsession.flush()
        interfaceitem = DataItem(order=0)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="1", key_id=ak.id))
        interfacesds.items.append(interfaceitem)
        interfaceitem = DataItem(order=1)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="2", key_id=ak.id))
        interfacesds.items.append(interfaceitem)

        params = {'task_worb':'w', 'interface_worb':'w', 'task_disallow':' ', 'interface_disallow':' ', 'task_order':' ', 'interface_order':' ', 'tasks_dataset': tasksds.id, 'interfaces_dataset': interfacesds.id}
        np = PermutationSet(name="test permset", params=params, owned_by=user.id, survey_id=survey.id, qsheet_id=qsheet2.id)
        survey.data_sets.append(np)
        user.data_sets.append(np)
        np.qsheets.append(qsheet2)

        tasksds = DataSet(name="three_tasks", owned_by=user.id, survey_id=survey.id)
        tasksds.attribute_keys.append(DataSetAttributeKey(key='name', order=0))
        survey.data_sets.append(tasksds)
        dbsession.flush()
        taskitem = DataItem(order=0)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="A", key_id=ak.id))
        tasksds.items.append(taskitem)
        taskitem = DataItem(order=1)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="B", key_id=ak.id))
        tasksds.items.append(taskitem)
        taskitem = DataItem(order=2)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="C", key_id=ak.id))
        tasksds.items.append(taskitem)

        interfacesds = DataSet(name="three_interfaces", owned_by=user.id, survey_id=survey.id)
        interfacesds.attribute_keys.append(DataSetAttributeKey(key='name', order=0))
        survey.data_sets.append(interfacesds)
        dbsession.flush()
        interfaceitem = DataItem(order=0)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="1", key_id=ak.id))
        interfacesds.items.append(interfaceitem)
        interfaceitem = DataItem(order=1)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="2", key_id=ak.id))
        interfacesds.items.append(interfaceitem)
        interfaceitem = DataItem(order=2)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="3", key_id=ak.id))
        interfacesds.items.append(interfaceitem)

        tasksds = DataSet(name="four_tasks", owned_by=user.id, survey_id=survey.id)
        tasksds.attribute_keys.append(DataSetAttributeKey(key='name', order=0))
        survey.data_sets.append(tasksds)
        dbsession.flush()
        taskitem = DataItem(order=0)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="A", key_id=ak.id))
        tasksds.items.append(taskitem)
        taskitem = DataItem(order=1)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="B", key_id=ak.id))
        tasksds.items.append(taskitem)
        taskitem = DataItem(order=2)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="C", key_id=ak.id))
        tasksds.items.append(taskitem)
        taskitem = DataItem(order=3)
        ak = tasksds.attribute_keys[0]
        taskitem.attributes.append(DataItemAttribute(value="D", key_id=ak.id))
        tasksds.items.append(taskitem)

        interfacesds = DataSet(name="four_interfaces", owned_by=user.id, survey_id=survey.id)
        interfacesds.attribute_keys.append(DataSetAttributeKey(key='name', order=0))
        survey.data_sets.append(interfacesds)
        dbsession.flush()
        interfaceitem = DataItem(order=0)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="1", key_id=ak.id))
        interfacesds.items.append(interfaceitem)
        interfaceitem = DataItem(order=1)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="2", key_id=ak.id))
        interfacesds.items.append(interfaceitem)
        interfaceitem = DataItem(order=2)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="3", key_id=ak.id))
        interfacesds.items.append(interfaceitem)
        interfaceitem = DataItem(order=3)
        ak = interfacesds.attribute_keys[0]
        interfaceitem.attributes.append(DataItemAttribute(value="4", key_id=ak.id))
        interfacesds.items.append(interfaceitem)

        survey.start = qsheet1
        QSheetTransition(source=qsheet1, target=qsheet2)
        # PAGE 3
        source="""<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="consent" title="Welcome">
  <pq:styles></pq:styles>
  <pq:scripts></pq:scripts>
  <pq:questions>
     <pq:question>
     <pq:type>confirm</pq:type>
     <pq:name>PermDone</pq:name>
     <pq:title>Participant ${pid_} imagine that iframe with ${perm} again then tick the box</pq:title>
     <pq:help></pq:help>
     <pq:required>true</pq:required>
     <pq:attribute name="further.value">done</pq:attribute>
     <pq:attribute name="further.label">Re-imagined</pq:attribute>
     </pq:question>
  </pq:questions>
</pq:qsheet>"""
        qsheet3 = QSheet(name='another_task_interface_page', title='Some more tasks...', styles='', scripts='')
        qsheet3.attributes.append(QSheetAttribute(key='repeat', value='repeat'))
        qsheet3.attributes.append(QSheetAttribute(key='data-items', value='1'))
        qsheet3.attributes.append(QSheetAttribute(key='control-items', value='0'))
        qsheet3.attributes.append(QSheetAttribute(key='show-question-numbers', value='no'))
        qsheet3.attributes.append(QSheetAttribute(key='task-count', value='2'))
        qsheet3.attributes.append(QSheetAttribute(key='interface-count', value='2'))
        load_questions(qsheet3, etree.fromstring(source), DBSession)
        survey.qsheets.append(qsheet3)
        dbsession.flush()
        survey.start = qsheet1
        QSheetTransition(source=qsheet1, target=qsheet2)
        QSheetTransition(source=qsheet2, target=qsheet3)
        notification = Notification(ntype='interval', value=60, recipient='paul@paulserver.paulsnetwork')
        survey.notifications.append(notification)
        notification = Notification(ntype='pcount', value=1, recipient='paul@paulserver.paulsnetwork')
        survey.notifications.append(notification)
        user.surveys.append(survey)
        DBSession.add(survey)
