# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''
try:
    import cPickle as pickle
except:
    import pickle
import transaction

from formencode import Schema, validators, api, foreach
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_

from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, DataItem)
from pyquest.renderer import render

@view_config(route_name='survey.results')
@render({'text/html': 'backend/results/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            qsheets = []
            for qsheet in survey.qsheets:
                qsheets.append({'qsid': unicode(qsheet.id),
                                'schema': pickle.loads(str(qsheet.schema))})
            participants = []
            for participant in survey.participants:
                participants.append(pickle.loads(str(participant.answers)))
            return {'survey': survey,
                    'qsheets': qsheets,
                    'participants': participants}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.results.download')
@render({'text/csv': ''})
def download(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if user and (survey.is_owned_by(user) or user.has_permission('survey.edit-all')):
            rows = []
            columns = ['qsid', 'did']
            if len(survey.data_items) > 0:
                for attr in survey.data_items[0].attributes:
                    columns.append(attr.key) 
            columns.append('question')
            columns.append('answer')
            for participant in survey.participants:
                answers = pickle.loads(str(participant.answers))
                for (qsid, value) in answers.items():
                    if 'items' in value:
                        for (did, questions) in value['items'].items():
                            for (question, answer) in questions.items():
                                if not question.endswith('_'):
                                    row = {'qsid': qsid,
                                           'did': did,
                                           'question': question,
                                           'answer': answer}
                                    if did != 'none':
                                        data_item = dbsession.query(DataItem).filter(DataItem.id==did).first()
                                        if data_item:
                                            for attr in data_item.attributes:
                                                row[attr.key] = attr.value
                                    rows.append(row)
            return {'columns': columns,
                    'rows': rows}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
