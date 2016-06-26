# -*- coding: utf-8 -*-
from pyramid.view import view_config
#from pywebtools.renderer import render
from sqlalchemy import func, and_

from pyquest.models import DBSession, Survey

def init(config):
    from pyquest.views import backend, admin
    config.add_static_view(name='static.files', path='pyquest:static')
    
    config.add_route('root', '/')
    admin.init(config)
    backend.init(config)
    config.add_route('survey.run', '/surveys/{seid}/run')
    config.add_route('survey.run.inactive', '/surveys/{seid}/inactive')
    config.add_route('survey.run.finished', '/surveys/{seid}/finished')


@view_config(route_name='root')
#@render({'text/html': 'root.html'})
def root(request):
    dbsession = DBSession()
    surveys = dbsession.query(Survey).filter(and_(Survey.status=='running', Survey.public==True)).limit(5)
    return {'surveys': surveys}
