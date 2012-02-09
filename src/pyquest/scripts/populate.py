# -*- coding: utf-8 -*-

import os
import sys
import transaction

from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

from pyquest.models import (DBSession, Base, Survey, QSheet, DataItem,
                            DataItemAttribute, User, Group, Permission)

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        user = User(u'mhall', u'm.mhall@sheffield.ac.uk', u'Archchancellor', u'test')
        group = Group(name='administrator')
        group.permissions.append(Permission(name='admin.configuration'))
        group.permissions.append(Permission(name='admin.users'))
        group.permissions.append(Permission(name='survey.edit-all'))
        group.permissions.append(Permission(name='survey.new'))
        user.groups.append(group)
        DBSession.add(user)
        survey = Survey(title='A test survey', content="""<pq:single qsid="1"/>
<pq:repeat qsid="2">
  <pq:data_items>
    <pq:data count="5"/>
    <pq:control count="0"/>
  </pq:data_items>
</pq:repeat>""")
        survey.owner = user
        qsheet = QSheet(title='Welcome', content="""<p>Thank you for participating
in this survey, your time is much appreciated.</p>
<p>Your data will be stored annonymously and in full compliance with the Data Protection Act.
Your data will only be used for reasearch purposes and will not be shared with anyone outside
the research group.</p>
<pq:confirm name="informed_consent" title="Please confirm that you have understood this" label="I confirm" required="true"/>""")
        survey.qsheets.append(qsheet)
        qsheet = QSheet(title='Rate this URL', content="""<p>Please rate the content
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
        survey.qsheets.append(qsheet)
        data_item = DataItem(order=1, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the first item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/1.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=2, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the second item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/2.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=3, control=True)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the third item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/3.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=4, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the fourth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/4.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=5, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the fifth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/5.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=6, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the sixth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/6.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=7, control=True)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the seventh item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/7.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=8, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the eighth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/8.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=9, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the ninth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/9.html'))
        survey.all_items.append(data_item)
        data_item = DataItem(order=10, control=False)
        data_item.attributes.append(DataItemAttribute(order=1, key='title', value='This is the tenth item'))
        data_item.attributes.append(DataItemAttribute(order=2, key='url', value='http://www.example.com/10.html'))
        survey.all_items.append(data_item)
        DBSession.add(survey)
        user = User(u'mahall', u'm.mhall@sheffield.ac.uk', u'Mark')
        DBSession.add(user)
        survey = Survey(title='Auth test')
        survey.owner = user
        qsheet = QSheet(title='A sheet', content='')
        survey.qsheets.append(qsheet)
        DBSession.add(survey)
