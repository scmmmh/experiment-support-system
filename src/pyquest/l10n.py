# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from gettext import GNUTranslations, NullTranslations
from pkg_resources import resource_listdir, resource_isdir, resource_stream

translators = {}

def init(settings):
    global translators
    for dir in resource_listdir('pyquest', 'l10n'):
        if resource_isdir('pyquest', 'l10n/%s' % (dir)):
            lang = {}
            try:
                frontend = resource_stream('pyquest', 'l10n/%s/LC_MESSAGES/frontend.mo' % (dir))
                if frontend:
                    lang['frontend'] = GNUTranslations(frontend)
            except IOError:
                pass
            try:
                backend = resource_stream('pyquest', 'l10n/%s/LC_MESSAGES/backend.mo' % (dir))
                if backend:
                    lang['backend'] = GNUTranslations(backend)
            except IOError:
                pass
            if len(lang) > 0:
                translators[dir] = lang

def get_translator(lang, domain):
    if lang in translators:
        if domain in translators[lang]:
            return translators[lang][domain]
    return NullTranslations()
