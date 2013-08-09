*************
Configuration
*************

PyQuestionnaire is configured using the .ini file created during :doc:`setup <setup>`.
In most cases, only the :ref:`core application configuration <configuration_core_application>`
will need to be changed, however you might want to also change the
:ref:`logging configuration <configuration_logging>`. Depending on how
PyQuestionnaire is :doc:`deployed <deployment>`, you can also configure how the
:ref:`internal default server <configuration_default_server>` is set up.

.. _configuration_core_application:
Core Application Configuration
==============================

The core application configuration is done in the ``[app:main]`` section. The
following core configuration options are available:

sqlalchemy.url
    The SQLAlchemy database connection string. See `SQLAlchemy connection string`_
    for details.

email.smtp_host
    The SMTP server host to use for sending e-mails.

Session configuration
---------------------

PyQuestionnaire uses `Beaker`_ to handle the session management. The following
configuration options are available

beaker.session.lock_dir
    The beaker session lock directory to use. Defaults to ``%(here)s/tmp``.

beaker.session.type
    The beaker session type to use. Defaults to ``cookie``.

beaker.session.key
    The name of the cookie used by the beaker sessions. Defaults to ``pyquest``.

beaker.session.encrypt_key
    The encryption key used by the beaker sessions. This is automatically
    generated when the configuration is created.
    
beaker.session.validate_key
    The validation key used by the beaker sessions. This is automatically
    generated when the configuration is created.

Pyramid framework configuration
-------------------------------

PyQuestionnaire uses the `Pyramid`_ web-application framework, which can be
configured using the following settings. These are set for a production
deployment and in most cases need not be changed. Particularly the debug
settings should be set to ``false`` in a production environment.

pyramid.reload_templates = false
    Whether to automatically re-load templates.
    
pyramid.debug_authorization = false
    Whether to debug the authorisation framework.
    
pyramid.debug_notfound = false
    Whether to debug not-found errors.
    
pyramid.debug_routematch = false
    Whether to debug route-matching errors.
    
pyramid.debug_templates = false
    Whether to debug template errors.
    
pyramid.default_locale_name = en
    The default locale used by `Pyramid`_.
    
pyramid.includes = pyramid_tm
    Additional modules used by `Pyramid`_. **MUST** include the ``pyramid_tm``
    module, which is needed for the database handling.
    
.. _configuration_logging:
Logging Configuration
=====================

Standard Python logging is used by all modules. Three loggers are used:
``root, pyquestionnaire, sqlalchemy`` and any configuration must be available
for all three. By default the configuration is set to log to the console.
For details on the logging setup, consult the core `Python logging`_ documentation.

.. _configuration_default_server:
Default Server Configuration
============================

`Pyramid`_ comes with a default web server (`Waitress`_), which is configured in the
``[server:main]`` section.

use
    The web-server to use. Defaults to ``egg:waitress#main``.

host
    Which IP addresses to listen on. Defaults to ``0.0.0.0``.
    
port
    The port to listen on. Defaults to ``6543``.

.. _SQLAlchemy connection string: http://docs.sqlalchemy.org/en/latest/dialects/
.. _Beaker: http://beaker.readthedocs.org/en/latest/
.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
.. _Python logging: http://docs.python.org/2/library/logging.config.html#configuration-file-format
.. _Waitress: http://docs.pylonsproject.org/projects/waitress/en/latest/
