# -*- coding: utf-8 -*-
'''
Created on 9 Feb 2012

@author: mhall
'''

from genshi.builder import tag
from pywebtools import ui

def main_menu(current, survey, request):
    return ui.menu([('overview', 'Overview', {'href': request.route_url('survey.overview', sid=survey.id)}),
                    ('data', 'Data', {'href': request.route_url('survey.data', sid=survey.id)}),
                    ('edit', 'Edit', {'href': request.route_url('survey.edit', sid=survey.id)}),
                    ('preview', 'Preview', {'href': request.route_url('survey.preview', sid=survey.id)}),
                    ('results', 'Results', {'href': request.route_url('survey.results', sid=survey.id)})],
                   current,
                   class_='level-1')
