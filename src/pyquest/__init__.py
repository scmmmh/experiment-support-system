# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
#from pywebtools import renderer
from sqlalchemy import engine_from_config

#from ess import views as ess_views
#from ess import models as ess_models

from pyquest.models import DBSession, check_database_version
from pyquest import l10n, views, helpers
from pyquest.notifier import Notifier

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['genshi.template_path'] = 'pyquest:templates/'
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    ess_models.DBSession.configure(bind=engine)
    check_database_version()
    session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings, session_factory=session_factory)
    config.include('kajiki.integration.pyramid')
    config.add_static_view('static', 'static', cache_max_age=3600)
    l10n.init(settings)
    template_defaults = {'h': helpers,
                         '_': l10n.get_translator('no', 'translations').ugettext}
    renderer.init(settings, {'text/html': template_defaults,
                             'application/xml': template_defaults})
    views.init(config)
    ess_views.init(config)
    config.scan()
    config.scan('ess')
    Notifier(settings).start()
    return config.make_wsgi_app()

