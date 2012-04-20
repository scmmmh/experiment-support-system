# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
import smtplib
import transaction

from email.mime.text import MIMEText
from formencode import Schema, validators, api
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
from pyramid.view import view_config
from random import randint

from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, User, Survey, Group, Permission)
from pyquest.renderer import render

class LoginSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    username = validators.UnicodeString(not_empty=True)
    password = validators.UnicodeString(not_empty=True)

class ForgottenPasswordSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    email = validators.Email(not_empty=True)

class UserNewSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    username = validators.UnicodeString(not_empty=True)
    display_name = validators.UnicodeString(not_empty=True)
    email = validators.Email(not_empty=True)
    
class UserEditSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    display_name = validators.UnicodeString(not_empty=True)
    email = validators.Email(not_empty=True)
    
class UserPermissionSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    
class PasswordChangeSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    password = validators.UnicodeString(not_empty=True)
    confirm_password = validators.UnicodeString(not_empty=True)
    
    chained_validators = [validators.FieldsMatch('password', 'confirm_password')]

@view_config(route_name='user.login')
@render({'text/html': 'admin/user/login.html'})
def login(request):
    if request.method == 'POST':
        try:
            params = LoginSchema().to_python(request.params)
            check_csrf_token(request, params)
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
        check_csrf_token(request, request.POST)
        del request.session['user-id']
        raise HTTPFound(request.route_url('root'))
    else:
        return {}

@view_config(route_name='user.forgotten_password')
@render({'text/html': 'admin/user/forgotten_password.html'})
def forgotten_password(request):
    if request.method == 'POST':
        check_csrf_token(request, request.POST)
        try:
            params = ForgottenPasswordSchema().to_python(request.POST)
            dbsession = DBSession()
            user = dbsession.query(User).filter(User.email==params['email']).first()
            if user:
                password = u''.join(unichr(randint(48, 122)) for _ in range(8))
                with transaction.manager:
                    user.new_password(password)
                    dbsession.add(user)
                user = dbsession.query(User).filter(User.email==params['email']).first()
                email = MIMEText("""You have requested a new password for %s. Your new password is:

%s

After logging in, please immediately change the password.

PyQuestionnaire Auto-Admin""" % (request.route_url('root'), password))
                email['Subject'] = 'New password for %s' % (request.route_url('root'))
                email['From'] = 'noreply@paths.sheffield.ac.uk'
                email['To'] = user.email
                smtp = smtplib.SMTP(request.registry.settings['email.smtp_host'])
                smtp.sendmail('noreply@paths.sheffield.ac.uk', user.email, email.as_string())
                smtp.quit()
            request.session.flash('A new password has been generated and e-mailed to the e-mail account you specified', 'info')
            raise HTTPFound(request.route_url('root'))
        except api.Invalid as e:
            e.params = request.params
            return {'e': e}
    else:
        return {}

@view_config(route_name='user')
@render({'text/html': 'admin/user/index.html'})
def index(request):
    user = current_user(request)
    if user and user.has_permission('admin.users'):
        dbsession = DBSession()
        users = dbsession.query(User).order_by(User.username)
        return {'users': users}
    else:
        redirect_to_login(request)

@view_config(route_name='user.new')
@render({'text/html': 'admin/user/new.html'})
def new(request):
    c_user = current_user(request)
    if c_user and c_user.has_permission('admin.users'):
        dbsession = DBSession()
        user = User('', '', '')
        if request.method == 'POST':
            try:
                params = UserNewSchema().to_python(request.POST)
                if params['csrf_token'] != request.session.get_csrf_token():
                    raise HTTPForbidden('Cross-site request forgery detected')
                with transaction.manager:
                    user.username = params['username']
                    user.display_name = params['display_name']
                    user.email = params['email']
                    dbsession.add(user)
                    dbsession.flush()
                    uid = user.id
                request.session.flash('User added', 'info')
                raise HTTPFound(request.route_url('user.view', uid=uid))
            except api.Invalid as e:
                e.params = request.POST
                return {'user': user,
                        'e': e}
        else:
            return {'user': user}
    else:
        redirect_to_login(request)

@view_config(route_name='user.view')
@render({'text/html': 'admin/user/view.html'})
def view(request):
    c_user = current_user(request)
    dbsession = DBSession()
    user = dbsession.query(User).filter(User.id==request.matchdict['uid']).first()
    if c_user and (c_user.id == user.id or c_user.has_permission('admin.users')):
        surveys = dbsession.query(Survey).filter(Survey.owned_by==request.matchdict['uid'])
        return {'user': user,
                'surveys': surveys}
    else:
        redirect_to_login(request)

@view_config(route_name='user.edit')
@render({'text/html': 'admin/user/edit.html'})
def edit(request):
    c_user = current_user(request)
    dbsession = DBSession()
    user = dbsession.query(User).filter(User.id==request.matchdict['uid']).first()
    if user:
        if c_user and (c_user.id == user.id or c_user.has_permission('admin.users')):
            if request.method == 'POST':
                try:
                    params = UserEditSchema().to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        user.display_name = params['display_name']
                        user.email = params['email']
                        dbsession.add(user)
                    request.session.flash('User preferences updated', 'info')
                    raise HTTPFound(request.route_url('user.view', uid=request.matchdict['uid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'user': user,
                            'e': e}
            else:
                return {'user': user}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='user.permissions')
@render({'text/html': 'admin/user/permissions.html'})
def permissions(request):
    c_user = current_user(request)
    dbsession = DBSession()
    if c_user and c_user.has_permission('admin.users'):
        user = dbsession.query(User).filter(User.id==request.matchdict['uid']).first()
        if user:
            permissions = dbsession.query(Permission).order_by(Permission.name)
            has_permissions = map(lambda p: unicode(p.id), user.permissions)
            groups = dbsession.query(Group).order_by(Group.title)
            has_groups = map(lambda g: unicode(g.id), user.groups)
            if request.method == 'POST':
                try:
                    schema = UserPermissionSchema()
                    schema.add_field('pid', validators.OneOf(map(lambda p: unicode(p.id), permissions), testValueList=True, if_missing=[], hideList=True))
                    schema.add_field('gid', validators.OneOf(map(lambda g: unicode(g.id), groups), testValueList=True, if_missing=[], hideList=True))
                    params = schema.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        user = dbsession.query(User).filter(User.id==request.matchdict['uid']).first()
                        user.groups = []
                        if isinstance(params['gid'], list):
                            for group in dbsession.query(Group).filter(Group.id.in_(params['gid'])):
                                user.groups.append(group)
                        else:
                            group = dbsession.query(Group).filter(Group.id==params['gid']).first()
                            if group:
                                user.groups.append(group)
                        user.permissions = []
                        if isinstance(params['pid'], list):
                            for permission in dbsession.query(Permission).filter(Permission.id.in_(params['pid'])):
                                user.permissions.append(permission)
                        else:
                            permission = dbsession.query(Permission).filter(Permission.id==params['pid']).first()
                            if permission:
                                user.permissions.append(permission)
                        dbsession.add(user)
                    request.session.flash('User permissions updated', 'info')
                    raise HTTPFound(request.route_url('user.view', uid=request.matchdict['uid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'user': user,
                            'permissions': permissions,
                            'has_permissions': has_permissions,
                            'groups': groups,
                            'has_groups': has_groups,
                            'e': e}
            else:
                return {'user': user,
                        'permissions': permissions,
                        'has_permissions': has_permissions,
                        'groups': groups,
                        'has_groups': has_groups}
        else:
            raise HTTPNotFound()
    else:
        redirect_to_login(request)

@view_config(route_name='user.delete')
@render({'text/html': 'admin/user/delete.html'})
def delete(request):
    c_user = current_user(request)
    if c_user and c_user.has_permission('admin.users'):
        dbsession = DBSession()
        user = dbsession.query(User).filter(User.id==request.matchdict['uid']).first()
        if user:
            if request.method == 'POST':
                if 'csrf_token' not in request.POST or request.POST['csrf_token'] != request.session.get_csrf_token():
                    raise HTTPForbidden('Cross-site request forgery detected')
                with transaction.manager:
                    dbsession.delete(user)
                request.session.flash('User deleted', 'info')
                raise HTTPFound(request.route_url('user'))
            else:
                return {'user': user}
        else:
            raise HTTPNotFound()
    else:
        redirect_to_login(request)

@view_config(route_name='user.password')
@render({'text/html': 'admin/user/password.html'})
def change_password(request):
    c_user = current_user(request)
    dbsession = DBSession()
    user = dbsession.query(User).filter(User.id==request.matchdict['uid']).first()
    if user:
        if c_user and c_user.id == user.id:
            if request.method == 'POST':
                try:
                    params = PasswordChangeSchema().to_python(request.POST)
                    if params['csrf_token'] != request.session.get_csrf_token():
                        raise HTTPForbidden('Cross-site request forgery detected')
                    with transaction.manager:
                        user.new_password(params['password'])
                        dbsession.add(user)
                    request.session.flash('Password changed', 'info')
                    raise HTTPFound(request.route_url('user.view', uid=request.matchdict['uid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'user': user,
                            'e': e}
            else:
                return {'user': user}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
