# -*- coding: utf-8 -*-
u"""
:mod:`pyquest.renderer` -- Genshi renderer for Pyramid
======================================================

This module provides the :class:`~pyquest.renderer.GenshiRendererFactory` that
is used to provide Genshi templating in the Pyramid WSGI framework.

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json
import mimeparse

from decorator import decorator
from genshi import XML
from genshi.template import TemplateLoader, loader
from genshi.filters.html import HTMLFormFiller
from pyramid.httpexceptions import HTTPNotAcceptable
from pyramid.request import Request
from pyramid.response import Response

from pyquest import helpers

genshi_loader = None

class RendererException(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return self.value


def init(settings):
    global genshi_loader
    if 'genshi.template_path' not in settings:
        raise RendererException('genshi.template_path not set in the configuration')
    path = settings['genshi.template_path']
    auto_reload = ('pyramid.reload_templates' in settings and settings['pyramid.reload_templates'] == 'true')
    if ':' in path:
        genshi_loader = TemplateLoader([loader.package(path[0:path.find(':')], path[path.find(':') + 1:])],
                                       auto_reload=auto_reload)
    else:
        genshi_loader = TemplateLoader(path.split(','),
                                       auto_reload=auto_reload)

def request_from_args(*args):
    if len(args) == 1 and isinstance(args[0], Request):
        return args[0]
    elif len(args) == 2 and isinstance(args[1], Request):
        return args[1]
    else:
        raise RendererException('No request found')
    
def template_defaults(request):
    return {'h': helpers,
            'r': request}

def match_response_type(view_content_types, request):
    accept_header = unicode(request.accept)
    if request.matchdict and 'ext' in request.matchdict and request.matchdict['ext']:
        if request.matchdict['ext'] == '.html':
            accept_header = 'text/html'
        elif request.matchdict['ext'] == '.json':
            accept_header = 'application/json'
    response_type = mimeparse.best_match(view_content_types.keys(), accept_header)
    if not response_type or response_type not in view_content_types:
        raise HTTPNotAcceptable()
    return response_type

def handle_html_response(request, response_template, result):
    template = genshi_loader.load(response_template)
    if 'e' in result:
        template = template.generate(**result) | HTMLFormFiller(data=result['e'].params)
    else:
        result['e'] = None
        template = template.generate(**result)
    response = Response(template.render('xhtml'))
    return response

def handle_json_response(request, result):
    del result['h']
    del result['r']
    if 'e' in result:
        del result['e']
    response = Response(json.dumps(result))
    return response

def render(content_types={}):
    def wrapper(f, *args, **kwargs):
        request = request_from_args(*args)
        result = template_defaults(request)
        result.update(f(*args, **kwargs))
        response_type = match_response_type(content_types, request)
        response_template = content_types[response_type]
        if response_type == 'application/json':
            response = handle_json_response(request, result)
        elif response_type == 'text/html':
            response = handle_html_response(request, response_template, result)
        response.content_type = response_type
        request.response.merge_cookies(response)
        return response
    return decorator(wrapper)
