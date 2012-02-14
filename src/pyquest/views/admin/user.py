# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
from formencode import Schema, validators, api

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from pyquest.helpers.auth import check_csrf_token
from pyquest.models import DBSession, User
from pyquest.renderer import render

class LoginValidator(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    username = validators.UnicodeString(not_empty=True)
    password = validators.UnicodeString(not_empty=True)

@view_config(route_name='user.login')
@render({'text/html': 'admin/user/login.html'})
def login(request):
    if request.method == 'POST':
        try:
            params = LoginValidator().to_python(request.params)
            check_csrf_token(request, params['csrf_token'])
            dbsession = DBSession()
            user = dbsession.query(User).filter(User.username==params['username']).first()
            if user.password_matches(params['password']):
                if 'redirect-to' in request.session:
                    redirect_to = request.session['redirect-to']
                else:
                    redirect_to = request.route_url('root')
                request.session['user-id'] = user.id
                raise HTTPFound(redirect_to)
            else:
                raise api.Invalid('Login failed', {}, None, error_dict={'username': 'Username unknown or password incorrect',
                                                                        'password': 'Username unknown or password incorrect'})
        except api.Invalid as e:
            e.params = request.params
            return {'e': e}
    else:
        return {}

@view_config(route_name='user.logout')
@render({'text/html': 'admin/user/logout.html'})
def logout(request):
    if request.method == 'POST':
        check_csrf_token(request, request.POST['csrf_token'])
        del request.session['user-id']
        raise HTTPFound(request.route_url('root'))
    else:
        return {}
