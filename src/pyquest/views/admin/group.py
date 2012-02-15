# -*- coding: utf-8 -*-
'''
Created on 15 Feb 2012

@author: mhall
'''
import transaction

from formencode import Schema, validators, api
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config

from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Group, Permission)
from pyquest.renderer import render

class GroupSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)

@view_config(route_name='group')
@render({'text/html': 'admin/group/index.html'})
def index(request):
    user = current_user(request)
    if user and user.has_permission('admin.groups'):
        dbsession = DBSession()
        groups = dbsession.query(Group).order_by(Group.title)
        return {'groups': groups}
    else:
        redirect_to_login(request)

@view_config(route_name='group.new')
@render({'text/html': 'admin/group/new.html'})
def new(request):
    user = current_user(request)
    dbsession = DBSession()
    if user and user.has_permission('admin.groups'):
        permissions = dbsession.query(Permission).order_by(Permission.title)
        if request.method == 'POST':
            try:
                schema = GroupSchema()
                schema.add_field('pid', validators.OneOf(map(lambda p: unicode(p.id), permissions), testValueList=True, if_missing=[], hideList=True))
                params = schema.to_python(request.POST)
                check_csrf_token(request, request.session.get_csrf_token())
                with transaction.manager:
                    group = Group(title=params['title'])
                    group.permissions = []
                    if 'pid' in params:
                        if isinstance(params['pid'], list):
                            for permission in dbsession.query(Permission).filter(Permission.id.in_(params['pid'])):
                                group.permissions.append(permission)
                        else:
                            permission = dbsession.query(Permission).filter(Permission.id==params['pid']).first()
                            if permission:
                                group.permissions.append(permission)
                    dbsession.add(group)
                    dbsession.flush()
                    gid = group.id
                request.session.flash('Group updated', 'info')
                raise HTTPFound(request.route_url('group.view', gid=gid))
            except api.Invalid as e:
                e.params = request.POST
                return {'group': Group(),
                            'permissions': permissions,
                            'e': e}
        else:
            return {'group': Group(),
                    'permissions': permissions}
    else:
        redirect_to_login(request)

@view_config(route_name='group.view')
@render({'text/html': 'admin/group/view.html'})
def view(request):
    user = current_user(request)
    dbsession = DBSession()
    if user and user.has_permission('admin.groups'):
        group = dbsession.query(Group).filter(Group.id==request.matchdict['gid']).first()
        if group:
            return {'group': group}
        else:
            raise HTTPNotFound()
    else:
        redirect_to_login(request)

@view_config(route_name='group.edit')
@render({'text/html': 'admin/group/edit.html'})
def edit(request):
    user = current_user(request)
    dbsession = DBSession()
    if user and user.has_permission('admin.groups'):
        group = dbsession.query(Group).filter(Group.id==request.matchdict['gid']).first()
        if group:
            permissions = dbsession.query(Permission).order_by(Permission.title)
            has_permissions = map(lambda p: unicode(p.id), group.permissions)
            if request.method == 'POST':
                try:
                    schema = GroupSchema()
                    schema.add_field('pid', validators.OneOf(map(lambda p: unicode(p.id), permissions), testValueList=True, if_missing=[], hideList=True))
                    params = schema.to_python(request.POST)
                    check_csrf_token(request, request.session.get_csrf_token())
                    with transaction.manager:
                        group = dbsession.query(Group).filter(Group.id==request.matchdict['gid']).first()
                        group.title = params['title']
                        group.permissions = []
                        if 'pid' in params:
                            if isinstance(params['pid'], list):
                                for permission in dbsession.query(Permission).filter(Permission.id.in_(params['pid'])):
                                    group.permissions.append(permission)
                            else:
                                permission = dbsession.query(Permission).filter(Permission.id==params['pid']).first()
                                if permission:
                                    group.permissions.append(permission)
                    request.session.flash('Group updated', 'info')
                    raise HTTPFound(request.route_url('group.view', gid=request.matchdict['gid']))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'group': group,
                            'permissions': permissions,
                            'has_permissions': has_permissions,
                            'e': e}
            else:
                return {'group': group,
                        'permissions': permissions,
                        'has_permissions': has_permissions}
        else:
            raise HTTPNotFound()
    else:
        redirect_to_login(request)

@view_config(route_name='group.delete')
@render({'text/html': 'admin/group/delete.html'})
def delete(request):
    user = current_user(request)
    dbsession = DBSession()
    if user and user.has_permission('admin.groups'):
        group = dbsession.query(Group).filter(Group.id==request.matchdict['gid']).first()
        if group:
            if request.method == 'POST':
                check_csrf_token(request, request.session.get_csrf_token())
                with transaction.manager:
                    dbsession.delete(group)
                request.session.flash('Group deleted', 'info')
                raise HTTPFound(request.route_url('group'))
            else:
                return {'group': group}
        else:
            raise HTTPNotFound()
    else:
        redirect_to_login(request)
