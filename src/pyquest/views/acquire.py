# -*- coding: utf-8 -*-
from random import sample

from pyramid.view import view_config
from sqlalchemy import and_

from pyquest.models import (DBSession, Survey, QSheet, DataItem)
from pyquest.renderer import render

@view_config(route_name='survey.run')
@render({'text/html': 'run/qsheet.html'})
def show_qsheet(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    items = []
    for db_item in sample(dbsession.query(DataItem).filter(DataItem.survey_id==request.matchdict['sid']).all(), 2):
        item = {}
        for attr in db_item.attributes:
            item[attr.key] = attr.value
        items.append(item)
    if survey and qsheet:
        return {'survey': survey,
                'qsheet': qsheet,
                'items': items}
