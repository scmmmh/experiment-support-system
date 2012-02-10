# -*- coding: utf-8 -*-
'''
Created on 9 Feb 2012

@author: mhall
'''

from genshi.builder import Markup
from pywebtools import ui

def breadcrumbs(items, request):
    items.insert(0, ('All my surveys', {'href': request.route_url('survey')}))
    return ui.breadcrumbs(items)

def main_menu(current, survey, request):
    return ui.menu([('back', [Markup('&larr;'),  ' All my surveys'], {'href': request.route_url('survey'), 'class': 'no-tab', 'style': 'font-weight:normal;'}),
                    ('survey', 'Survey', {'href': request.route_url('survey.view', sid=survey.id)}),
                    ('pages', 'Pages', {'href': request.route_url('survey.qsheet', sid=survey.id)}),
                    ('data', 'Data', {'href': request.route_url('survey.data', sid=survey.id)}),
                    ('preview', 'Preview', {'href': request.route_url('survey.preview', sid=survey.id)}),
                    ('results', 'Results', {'href': request.route_url('survey.results', sid=survey.id)})],
                   current,
                   class_='level-1')
