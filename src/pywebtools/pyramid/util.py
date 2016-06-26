# -*- coding: utf-8 -*-
"""
##########################################################################
:mod:`pywebtools` -- Utilities for Kajiki, Pyramid, Formencode, SQLAlchemy
##########################################################################

Utility functions for use with the Pyramid framework.

* :func:`~pywebtools.pyramid.util.request_from_args` is useful with decorators
  or any other function where you do not know which argument is the Pyramid
  :class:`~pyramid.request.Request`.
* :func:`~pywebtools.pyramid.util.get_config_setting` provides easy access
  to configuration settings set in the [app:main] section of the INI file.
* :func:`~pywebtools.pyramid.util.require_method` is a decorator to enforce
  HTTP methods.
* :class:`~pywebtools.pyramid.util.MenuBuilder` is a helper class to generate
  the menu structure used with :func:`~pywebtools.kajiki.menubar`.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from decorator import decorator
from pyramid.request import Request
from pyramid.httpexceptions import HTTPMethodNotAllowed


def request_from_args(*args):
    """Returns the :class:`~pyramid.request.Request` from the function
    parameters list ``args``.

    :param args: The parameters passed to a function
    :return: The request object
    :r_type: :class:`~pyramid.request.Request`
    """
    for arg in args:
        if isinstance(arg, Request):
            return arg
    raise Exception('No request found')


def require_method(methods):
    """Checks that the current request method is in the list of ``methods``
    that are allowed for the given request.

    :param methods: The list of valid request methods
    :type methods: `list` of `unicode`
    """
    if not isinstance(methods, list):
        methods = [methods]

    def wrapper(f, *args, **kwargs):
        request = request_from_args(*args)
        if request.method in methods:
            return f(*args, **kwargs)
        else:
            raise HTTPMethodNotAllowed()
    return decorator(wrapper)


def convert_type(value, target_type, default=None):
    """Attempts to convert the ``value`` to the given ``target_type``. Will
    return ``default`` if the conversion fails.

    Supported ``target_type`` values are:

    * `int` -- Convert to an integer value
    * `boolean` -- Convert to a boolean value (``True`` if the value is the
      ``unicode`` string "true" in any capitalisation
    * `list` -- Convert to a list, splitting on line-breaks and commas

    :param value: The value to convert
    :type value: `unicode`
    :param target_type: The target type to convert to
    :type target_type: `unicode`
    :param default: The default value if the conversion fails
    :return: The converted value
    """
    if target_type == 'int':
        try:
            return int(value)
        except ValueError:
            return default
    elif target_type == 'boolean':
        if value and value.lower() == 'true':
            return True
        else:
            return False
    elif target_type == 'list':
        return [v.strip() for line in value.split('\n') for v in line.split(',')]
    if value:
        return value
    else:
        return default


# Cached application settings for faster access
CACHED_SETTINGS = {}


def get_config_setting(request, key, target_type=None, default=None):
    """Gets a configuration setting from the application configuration.
    Settings are cached for faster access.

    :param request: The request used to access the configuration settings
    :type request: :class:`~pyramid.request.Request`
    :param key: The configuration key
    :type key: `unicode`
    :param target_type: If specified, will convert the configuration setting
                        to the given type using :func:`~pywebtools.pyramid.util.convert_type`
    :type default: The default value to return if there is no setting with the
                   given key
    :return: The configuration setting value or ``default``
    """
    global CACHED_SETTINGS
    if key in CACHED_SETTINGS:
        return CACHED_SETTINGS[key]
    else:
        if key in request.registry.settings:
            if target_type:
                CACHED_SETTINGS[key] = convert_type(request.registry.settings[key], target_type, default=default)
            else:
                CACHED_SETTINGS[key] = request.registry.settings[key]
        else:
            CACHED_SETTINGS[key] = default
        return get_config_setting(request, key, target_type=target_type, default=default)


class MenuBuilder(object):
    """The :class:`~pywebtools.pyramid.util.MenuBuilder` helps with creating the ``list``
    structure used for creating the icon-menubar used with :func:`~pywebtools.kajiki.menubar`.
    Call :func:`~pywebtools.pyramid.util.MenuBuilder.group` to start a new group of menu items.
    Call :func:`~pywebtools.pyramid.util.MenuBuilder.item` to add a menu item to the current group.
    :func:`~pywebtools.pyramid.util.MenuBuilder.generate` then generates the final structure for use in the menubar.
    """

    def __init__(self):
        self._groups = []
        self._group = None

    def group(self, label, icon=None):
        """Add a new group to the list of groups in this :class:`~pywebtools.pyramid.util.MenuBuilder`.

        :param label: The menu group's label
        :type label: `unicode`
        :param icon: The optional icon for this group. An icon must be provided in order to
                     enable highlighting of menu items
        :type icon: `unicode`
        """
        if self._group and self._group['items']:
            self._groups.append(self._group)
        self._group = {'label': label,
                       'items': []}
        if icon:
            self._group['icon'] = icon

    def menu(self, label, href, icon=None, highlight=False, attrs=None):
        """Add a new menu item to the current group. Will create a new group with an empty
        label if :func:`~pywebtools.pyramid.util.MenuBuilder.group` has not been called.

        :param label: The menu item's label
        :type label: `unicode`
        :param href: The URL that the menu item loads
        :type href: `unicode`
        :param icon: The optional icon for this menu item
        :type icon: `unicode`
        :param highlight: Whether to highlight the menu item by displaying it at the top level
        :type highlight: `boolean`
        :param attrs: Additional attributes to set for the menu item link
        :type attrs: :class:`dict`
        """
        if not self._group:
            self._group = {'label': '',
                           'items': []}
        if attrs:
            attrs['href'] = href
        else:
            attrs = {'href': href}
        item = {'visible': True,
                'label': label,
                'attrs': attrs}
        if icon:
            item['icon'] = icon
        if highlight:
            item['highlight'] = True
        self._group['items'].append(item)

    def generate(self):
        """Generate the final menu structure.

        :return: The list of menu groups with their menu items
        :return_type: ``list`` of menu groups
        """
        if self._group and self._group['items']:
            self._groups.append(self._group)
            self._group = None
        return self._groups
