# -*- coding: utf-8 -*-
u"""
:mod:`pyquest.renderer` -- Genshi renderer for Pyramid
======================================================

This module provides the :class:`~pyquest.renderer.GenshiRendererFactory` that
is used to provide Genshi templating in the Pyramid WSGI framework.

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import csv
import json
import mimeparse

from decorator import decorator
from genshi import filters
from genshi.template import TemplateLoader, loader
from gettext import NullTranslations
from pyramid.httpexceptions import HTTPNotAcceptable
from pyramid.request import Request
from pyramid.response import Response
from StringIO import StringIO

from pyquest import helpers
from pyquest.l10n import get_translator

genshi_loader = None

class RendererException(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return self.value

def init(settings):
    def template_loaded(template):
        if 'frontend' in template.filename:
            translator = filters.Translator(NullTranslations())
            translator.setup(template)
    global genshi_loader
    if 'genshi.template_path' not in settings:
        raise RendererException('genshi.template_path not set in the configuration')
    path = settings['genshi.template_path']
    auto_reload = ('pyramid.reload_templates' in settings and settings['pyramid.reload_templates'] == 'true')
    if ':' in path:
        genshi_loader = TemplateLoader([loader.package(path[0:path.find(':')], path[path.find(':') + 1:])],
                                       auto_reload=auto_reload,
                                       callback=template_loaded)
    else:
        genshi_loader = TemplateLoader(path.split(','),
                                       auto_reload=auto_reload,
                                       callback=template_loaded)

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
        if request.matchdict['ext'] == 'html':
            accept_header = 'text/html'
        elif request.matchdict['ext'] == 'json':
            accept_header = 'application/json'
        elif request.matchdict['ext'] == 'csv':
            accept_header = 'text/csv'
        elif request.matchdict['ext'] == 'xml':
            accept_header = 'application/xml'
    response_type = mimeparse.best_match(view_content_types.keys(), accept_header)
    if not response_type or response_type not in view_content_types:
        raise HTTPNotAcceptable()
    return response_type

def handle_html_response(request, response_template, result):
    template = genshi_loader.load(response_template)
    if 'frontend' in template.filename:
        if 'survey' in result:
            translator = get_translator(result['survey'].language, 'frontend')
        else:
            translator = NullTranslations()
        template.filters[0].translate = translator
        result['_'] = translator.ugettext
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
        result['e'] = result['e'].error_dict
    response = Response(json.dumps(result))
    return response

def handle_csv_response(request, result):
    f = StringIO()
    writer = csv.DictWriter(f, result['columns'])
    writer.writeheader()
    for row in result['rows']:
        writer.writerow(row)
    response = Response(unicode(f.getvalue()))
    f.close()
    return response

def handle_xml_response(request, response_template, result):
    template = genshi_loader.load(response_template)
    template = template.generate(**result)
    response = Response(template.render('xml'))
    return response

def render(content_types={}, allow_cache=True):
    def wrapper(f, *args, **kwargs):
        request = request_from_args(*args)
        result = template_defaults(request)
        result.update(f(*args, **kwargs))
        response_type = match_response_type(content_types, request)
        response_template = content_types[response_type]
        if response_type == 'application/json':
            response = handle_json_response(request, result)
            response.cache_control = 'no-cache'
            response.pragma = 'no-cache'
            response.expires = '0'
        elif response_type == 'text/html':
            response = handle_html_response(request, response_template, result)
        elif response_type == 'text/csv':
            response = handle_csv_response(request, result)
        elif response_type == 'application/xml':
            response = handle_xml_response(request, response_template, result)
        response.content_type = response_type
        request.response.merge_cookies(response)
        if not allow_cache:
            response.cache_control = 'no-cache'
            response.pragma = 'no-cache'
            response.expires = '0'
        return response
    return decorator(wrapper)

class HTMLFormFiller(object):
    """A stream filter that can populate HTML forms from a dictionary of values.
    Adds support for HTML5 form elements and multi-selection of checkboxes.
    
    >>> from genshi.input import HTML
    >>> html = HTML('''<form>
    ...   <p><input type="text" name="foo" /></p>
    ... </form>''')
    >>> filler = HTMLFormFiller(data={'foo': 'bar'})
    >>> print(html | filler)
    <form>
      <p><input type="text" name="foo" value="bar"/></p>
    </form>
    """
    # TODO: only select the first radio button, and the first select option
    #       (if not in a multiple-select)
    # TODO: only apply to elements in the XHTML namespace (or no namespace)?

    def __init__(self, name=None, id=None, data=None, passwords=False):
        """Create the filter.
        
        :param name: The name of the form that should be populated. If this
                     parameter is given, only forms where the ``name`` attribute
                     value matches the parameter are processed.
        :param id: The ID of the form that should be populated. If this
                   parameter is given, only forms where the ``id`` attribute
                   value matches the parameter are processed.
        :param data: The dictionary of form values, where the keys are the names
                     of the form fields, and the values are the values to fill
                     in.
        :param passwords: Whether password input fields should be populated.
                          This is off by default for security reasons (for
                          example, a password may end up in the browser cache)
        :note: Changed in 0.5.2: added the `passwords` option
        """
        self.name = name
        self.id = id
        if data is None:
            data = {}
        self.data = data
        self.passwords = passwords

    def __call__(self, stream):
        """Apply the filter to the given stream.
        
        :param stream: the markup event stream to filter
        """
        in_form = in_select = in_option = in_textarea = False
        select_value = option_value = textarea_value = None
        option_start = None
        option_text = []
        no_option_value = False

        for kind, data, pos in stream:

            if kind is filters.html.START:
                tag, attrs = data
                tagname = tag.localname

                if tagname == 'form' and (
                        self.name and attrs.get('name') == self.name or
                        self.id and attrs.get('id') == self.id or
                        not (self.id or self.name)):
                    in_form = True

                elif in_form:
                    if tagname == 'input':
                        type = attrs.get('type', '').lower()
                        if type in ('checkbox', 'radio'):
                            name = attrs.get('name')
                            if name and name in self.data:
                                try:
                                    value = self.data.getall(name)
                                except AttributeError:
                                    value = self.data[name]
                                declval = attrs.get('value')
                                checked = False
                                if isinstance(value, (list, tuple)):
                                    if declval:
                                        checked = declval in [unicode(v) for v
                                                              in value]
                                    else:
                                        checked = any(value)
                                else:
                                    if declval:
                                        checked = declval == unicode(value)
                                    elif type == 'checkbox':
                                        checked = bool(value)
                                if checked:
                                    attrs |= [(filters.html.QName('checked'), 'checked')]
                                elif 'checked' in attrs:
                                    attrs -= 'checked'
                        elif type in ('', 'hidden', 'text', 'number', 'email', 'url', 'date', 'time', 'datetime', 'month') \
                                or type == 'password' and self.passwords:
                            name = attrs.get('name')
                            if name and name in self.data:
                                value = self.data[name]
                                if isinstance(value, (list, tuple)):
                                    value = value[0]
                                if value is not None:
                                    attrs |= [
                                        (filters.html.QName('value'), unicode(value))
                                    ]
                    elif tagname == 'select':
                        name = attrs.get('name')
                        if name in self.data:
                            select_value = self.data[name]
                            in_select = True
                    elif tagname == 'textarea':
                        name = attrs.get('name')
                        if name in self.data:
                            textarea_value = self.data.get(name)
                            if isinstance(textarea_value, (list, tuple)):
                                textarea_value = textarea_value[0]
                            in_textarea = True
                    elif in_select and tagname == 'option':
                        option_start = kind, data, pos
                        option_value = attrs.get('value')
                        if option_value is None:
                            no_option_value = True
                            option_value = ''
                        in_option = True
                        continue
                yield kind, (tag, attrs), pos

            elif in_form and kind is filters.html.TEXT:
                if in_select and in_option:
                    if no_option_value:
                        option_value += data
                    option_text.append((kind, data, pos))
                    continue
                elif in_textarea:
                    continue
                yield kind, data, pos

            elif in_form and kind is filters.html.END:
                tagname = data.localname
                if tagname == 'form':
                    in_form = False
                elif tagname == 'select':
                    in_select = False
                    select_value = None
                elif in_select and tagname == 'option':
                    if isinstance(select_value, (tuple, list)):
                        selected = option_value in [unicode(v) for v
                                                    in select_value]
                    else:
                        selected = option_value == unicode(select_value)
                    okind, (tag, attrs), opos = option_start
                    if selected:
                        attrs |= [(filters.html.QName('selected'), 'selected')]
                    elif 'selected' in attrs:
                        attrs -= 'selected'
                    yield okind, (tag, attrs), opos
                    if option_text:
                        for event in option_text:
                            yield event
                    in_option = False
                    no_option_value = False
                    option_start = option_value = None
                    option_text = []
                elif tagname == 'textarea':
                    if textarea_value:
                        yield filters.html.TEXT, unicode(textarea_value), pos
                    in_textarea = False
                yield kind, data, pos

            else:
                yield kind, data, pos
