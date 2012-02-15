# -*- coding: utf-8 -*-

def init(config):
    config.add_route('user', '/users')
    config.add_route('user.login', '/users/login')
    config.add_route('user.logout', '/users/logout')
    config.add_route('user.forgotten_password', '/users/forgotten_password')
    config.add_route('user.new', '/users/new')
    config.add_route('user.view', '/users/{uid}')
    config.add_route('user.edit', '/users/{uid}/edit')
    config.add_route('user.rights', '/users/{uid}/rights')
    config.add_route('user.delete', '/users/{uid}/delete')
    config.add_route('user.password', '/users/{uid}/password')
