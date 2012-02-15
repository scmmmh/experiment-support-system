# -*- coding: utf-8 -*-

def init(config):
    config.add_route('user', '/users')
    config.add_route('user.login', '/users/login')
    config.add_route('user.logout', '/users/logout')
    config.add_route('user.forgotten_password', '/users/forgotten_password')
    config.add_route('user.new', '/users/new')
    config.add_route('user.view', '/users/{uid}')
    config.add_route('user.edit', '/users/{uid}/edit')
    config.add_route('user.permissions', '/users/{uid}/permissions')
    config.add_route('user.delete', '/users/{uid}/delete')
    config.add_route('user.password', '/users/{uid}/password')
    config.add_route('group', '/admin/groups')
    config.add_route('group.new', '/admin/groups/new')
    config.add_route('group.view', '/admin/groups/{gid}')
    config.add_route('group.edit', '/admin/groups/{gid}/edit')
    config.add_route('group.delete', '/admin/groups/{gid}/delete')
    
