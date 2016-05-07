from . import frontend

def init(config):
    config.add_static_view(name='ess_static', path='ess:static', cache_max_age=3600)
    frontend.init(config)
