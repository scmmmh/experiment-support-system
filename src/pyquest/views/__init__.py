# -*- coding: utf-8 -*-

def init(config):
    from pyquest.views import backend, admin
    config.add_route('root', '/')
    config.add_static_view(name='static.files', path='pyquest:static')
    
    admin.init(config)
    backend.init(config)
    config.add_route('survey.run', '/surveys/{sid}/run')
    config.add_route('survey.run.inactive', '/surveys/{sid}/inactive')
    config.add_route('survey.run.finished', '/surveys/{sid}/finished')
