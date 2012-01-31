# -*- coding: utf-8 -*-

def init(config):
    from pyquest.views import backend
    config.add_route('root', '/')
    backend.init(config)
    config.add_route('user.login', '/users/login')
    config.add_route('survey.run', '/surveys/{sid}/run/{qsid}')
    config.add_static_view(name='static.files', path='pyquest:static')