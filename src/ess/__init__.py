from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pywebtools.sqlalchemy import DBSession, check_database_version
from sqlalchemy import engine_from_config

from ess import views
from ess.models import DB_VERSION


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    check_database_version(DB_VERSION)
    session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings, session_factory=session_factory)
    config.include('kajiki.integration.pyramid')
    config.add_static_view('static', 'static', cache_max_age=3600)
    views.init(config)
    config.scan()
    return config.make_wsgi_app()
