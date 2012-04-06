# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from sqlalchemy import engine_from_config

from pyquest.models import DBSession, check_database_version
from pyquest import l10n, renderer, views

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    check_database_version()
    session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings, session_factory=session_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)
    l10n.init(settings)
    renderer.init(settings)
    views.init(config)
    config.scan()
    return config.make_wsgi_app()

