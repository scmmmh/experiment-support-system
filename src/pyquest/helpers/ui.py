# -*- coding: utf-8 -*-
'''
Created on 9 Feb 2012

@author: mhall
'''

from genshi.builder import Markup
from pywebtools import ui

from pyquest.util import get_config_setting

def breadcrumbs(items, request):
    items.insert(0, (get_config_setting(request, 'app.title', default='Experiment Support System'), {'href': request.route_url('root')}))
    return ui.breadcrumbs(items)
    
def survey_breadcrumbs(items, request):
    items.insert(0, ('All my surveys', {'href': request.route_url('survey')}))
    return breadcrumbs(items, request)

def main_menu(current, survey, request):
    menu_items = [('back', [Markup('&larr;'),  ' All my experiments'], {'href': request.route_url('survey'), 'class': 'no-tab', 'style': 'font-weight:normal;'}),
                  ('survey', 'Survey', {'href': request.route_url('survey.view', sid=survey.id)}),
                  ('data', 'Data', {'href': request.route_url('data.list', sid=survey.id)}),
                  ('preview', 'Preview', {'href': request.route_url('survey.preview', sid=survey.id)}),
                  ('results', 'Results', {'href': request.route_url('survey.results', sid=survey.id)})]
    if survey.status == 'testing':
        menu_items.append(('test', 'Test', {'href': request.route_url('survey.run', seid=survey.external_id)}))
    return ui.menu(menu_items,
                   current,
                   class_='level-1')

def pager(page, pages, request):
    query = {'show': 'all'}
    if 'show' in request.params:
        if request.params['show'] == 'data':
            query['show'] = 'data'
        elif request.params['show'] == 'control':
            query['show'] = 'control'
    base_url = request.current_route_url(_query=query)
    return ui.pager(base_url, page, pages)
