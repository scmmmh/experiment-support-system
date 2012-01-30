# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
from pyramid.httpexceptions import HTTPFound

from pyquest.models import DBSession, User

def current_user(request):
    if 'user-id' in request.session:
        dbsession = DBSession()
        return dbsession.query(User).filter(User.id==request.session['user-id']).first()
    else:
        return None

def redirect_to_login(request):
    request.session.flash('You do not have sufficient rights to access this area', 'auth')
    request.session['redirect-to'] = request.current_route_url()
    raise HTTPFound(request.route_url('user.login'))
