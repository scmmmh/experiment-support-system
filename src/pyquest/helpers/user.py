# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
import transaction

from genshi.builder import tag
from pyramid.httpexceptions import HTTPFound

from pyquest.models import DBSession, User, Preference

def current_user(request):
    if 'user-id' in request.session:
        dbsession = DBSession()
        user = dbsession.query(User).filter(User.id==request.session['user-id']).first()
        if user:
            user.logged_in = True
        return user
    else:
        return None

def redirect_to_login(request):
    request.session.flash('You do not have sufficient rights to access this area', 'auth')
    request.session['redirect-to'] = request.current_route_url()
    raise HTTPFound(request.route_url('user.login'))

def menu(request):
    user = current_user(request)
    if user:
        return tag.nav(tag.ul(tag.li(tag.a(tag.strong('Surveys'), href=request.route_url('survey'))),
                              tag.li(tag.a('Preferences', href=request.route_url('user.edit', uid=user.id))),
                              tag.li(tag.a('Change Password', href=request.route_url('user.password', uid=user.id))),
                              tag.li(tag.a('Logout', href=request.route_url('user.logout'), class_='post-submit', data_confirm='no-confirm'))),
                       class_='user-menu right')
    else:
        return tag.nav(tag.ul(tag.li(tag.a('Login', href=request.route_url('user.login')))),
                       class_='user-menu right')

def tooltips(request, tooltip=None, tooltip_new=None):
    user = current_user(request)
    if not user or (not tooltip and not tooltip_new) or not user.preference('show.tooltips', default=True, data_type='boolean'):
        return None
    tooltips = {}
    if tooltip:
        tooltips['title'] = tooltip
    if tooltip_new:
        if not user.preference('tooltip_new.%s.seen' % tooltip_new[0], default=False, data_type='boolean'):
            tooltips['data-tooltip-new'] = tooltip_new[1]
            dbsession = DBSession()
            with transaction.manager:
                dbsession.add(Preference(user_id=user.id, key='tooltip_new.%s.seen' % tooltip_new[0], value='True'))
    return tooltips



