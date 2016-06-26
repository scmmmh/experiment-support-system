"""
###################################################################################
:mod:`pywebtools.pyramid.auth` -- Authentication Framework for Pyramid + SQLAlchemy
###################################################################################

The :mod:`pywebtools.pyramid.auth` module provides an authentication framework for use
with Pyramid and SQLAlchemy. It provides a :class:`~pywebtools.pyramid.auth.models.User`
model plus all the views needed to handle registration, login, logout,
and password retrieval. The workflow that it implements is registration -> confirmation
via e-mail -> password reset -> login -> forgotten password -> password reset.

The framework is configurable via the parameters passed to the :func:`~pywebtools.pyramid.auth.init`
function.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from pywebtools.pyramid.auth import views

active_urls = {'user.login': '/users/login',
               'user.logout': '/users/logout',
               'user.register': '/users/register',
               'user.confirm': '/users/confirm/{token}',
               'user.forgotten_password': '/users/forgotten-password',
               'user.reset_password': '/users/reset-password/{token}'}


def init(config, renderers=None, urls=None, redirects=None, callbacks=None):
    """Initialises the authentication framework.

    Routes that can have renderers attached via ``renderers`, redirects
    via ``redirects``, and can have their URLs changed via ``urls``:

    * user.login - :func:`~pywebtools.pyramid.auth.views.login`
    * user.logout - :func:`~pywebtools.pyramid.auth.views.logout`
    * user.register - :func:`~pywebtools.pyramid.auth.views.register`
    * user.confirm - :func:`~pywebtools.pyramid.auth.views.confirm` (no redirection)
    * user.forgotten_password - :func:`~pywebtools.pyramid.auth.views.forgotten_password`
    * user.reset_password - :func:`~pywebtools.pyramid.auth.views.reset_password`

    If no renderer is provided for a route, then the route will not be registered.

    The following callbacks can be registered via ``callbacks``:

    * user.created - called from :func:`~pywebtools.pyramid.auth.views.register` and
      :func:`~pywebtools.pyramid.auth.views.forgotten_password`
    * user.validated - called from :func:`~pywebtools.pyramid.auth.views.confirm`
    * user.password_reset - called from :func:`~pywebtools.pyramid.auth.views.forgotten_password`
    * user.password_reset_failed - called from :func:`~pywebtools.pyramid.auth.views.forgotten_password`
    * user.password_reset_complete - called from :func:`~pywebtools.pyramid.auth.views.reset_password`

    :param config: The Pyramid configuration object to use to set up the configuration
    :type config: :class:`~pyramid.config.Configurator`
    :param renderers: Renderers to attach to the available views
    :type renderers: ``dict``
    :param urls: Alternative URLs to use
    :type urls: ``dict``
    :param redirects: Redirect routes that are used after any request has been completed
    :type redirects: ``dict``
    :param callbacks: Callbacks that are called for certain actions on the user
    :type callbacks: ``dict``
    """
    if urls is not None:
        active_urls.update(urls)
    if redirects:
        views.active_redirects.update(redirects)
    if callbacks:
        views.active_callbacks.update(callbacks)
    for key, value in active_urls.items():
        config.add_route(key, value)
        if key in renderers:
            config.add_view('pywebtools.pyramid.auth.views.%s' % (key[key.rfind('.') + 1:]),
                            route_name=key,
                            renderer=renderers[key])
