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
        user.groups.append(group)
        DBSession.add(user)
        survey = Survey(title='A test survey')
        survey.owner = user
        qsheet = QSheet(order=1, title='Sheet 1', content="""<p>${Text}</p>
<p style="text-align:center;"><img src="${URL}" /></p>
<p style="text-align:center;"><strong>Caption:</strong> ${Caption}</p>
<pq:rating name="familiar" title="How familiar are you with the topic?" min_value="1" min_title="Not at all" max_value="9" max_title="Very"/>
<pq:rating min="1" max="5" hide_extra_labels="true" name="appropriate" title="How appropriate is the image?"/>
<pq:rating name="support" title="How well does the image support the core ideas of the paragraph?">
  <pq:option value="1" title="Not at all"/>
  <pq:option value="2"/>
  <pq:option value="3"/>
  <pq:option value="4"/>
  <pq:option value="5" title="Perfectly"/>
</pq:rating>
<pq:rating_group name="visual" title="About the image">
  <pq:option value="1" title="Not at all"/>
  <pq:option value="2"/>
  <pq:option value="3"/>
  <pq:option value="4"/>
  <pq:option value="5" title="Very"/>
  <pq:rating name="interest" title="How visually interesting is the image?"/>
  <pq:rating name="click" title="How likely are you to click on the image to find out more?"/>
</pq:rating_group>
<pq:email name="email" title="Please provide your e-mail address" required="true"/>
<pq:url name="url" title="My homepage"/>
<pq:number name="age" title="How old are you?" min_value="18" max_value="72" step="1"/>
<pq:date name="birthday" title="Please provide your birthday"/>
<pq:month name="current_month" title="What is the current month?"/>
<pq:datetime name="now" title="Provide the date and time you wish?"/>
<pq:time name="wakeup_time" title="When did you wake up today?"/>
<pq:short_text name="name" title="What is your name?"/>
<pq:long_text name="interests" title="Please briefly describe yourself"/>
<pq:selectchoice name="help" title="Do you need help?">
  <pq:option value="yes" title="Yes"/>
  <pq:option value="no" title="No"/>
</pq:selectchoice>
<pq:listchoice name="tv" title="Do you like TV?">
  <pq:option value="yes" title="Yes"/>
  <pq:option value="bit" title="A bit"/>
  <pq:option value="no" title="No"/>
</pq:listchoice>
<pq:multichoice name="likes" title="What do you like doing at the weekend?">
  <pq:option value="walking" title="Walking"/>
  <pq:option value="eating" title="Eating"/>
  <pq:option value="drinking" title="Drinking"/>
  <pq:option value="dancing" title="Dancing"/>
</pq:multichoice>
<pq:multichoice_group name="doing" title="What do you do when?">
  <pq:option value="daytime" title="During the week - daytime"/>
  <pq:option value="evening" title="During the week - evenings"/>
  <pq:option value="weekend" title="Weekend"/>
  <pq:multichoice name="books" title="Reading books"/>
  <pq:multichoice name="internet" title="Surfing the internet"/>
  <pq:multichoice name="telephone" title="Telephoning"/>
  <pq:multichoice name="sleep" title="Sleeping"/>
</pq:multichoice_group>
<pq:confirm name="terms" title="Please confirm that you agree to the terms."/>
<pq:ranking name="importance" title="Please rank the following items">
  <pq:option value="cat" title="Cat"/>
  <pq:option value="dog" title="Dog"/>
  <pq:option value="mouse" title="Mouse"/>
  <pq:option value="bird" title="Bird"/>
</pq:ranking>
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
