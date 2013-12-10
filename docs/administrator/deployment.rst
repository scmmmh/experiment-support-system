**********
Deployment
**********

In-production deployment has been tested using `Apache2`_ and `mod_wsgi`_.
For other deployment scenarios, please consult the `pyramid deployment`_
documentation.

Deploying with Apache2 & mod_wsgi
=================================

To deploy the Experiment Support System via `Apache2`_ and `mod_wsgi`_ add the
following settings to the VirtualHost configuration::

    WSGIDaemonProcess pyquest user=www-data group=www-data processes=1 threads=10 python-path=/path/to/virtualenv/lib/python2.7/site-packages
    WSGIScriptAlias /pyquest /path/to/the/application.wsgi
    <Location /pyquest>
        WSGIProcessGroup pyquest
    </Location>

**Note**: Leave the ``processes`` value at 1. Use the ``threads`` option to
specify how many parallel requests to support. 

Then create the following script to to run the application via `WSGI`_. Adapt
it by replacing the paths with the paths to where the Experiment Support System
is installed::

    import os
    os.chdir(os.path.dirname(__file__))
    import site
    import sys

    # Remember original sys.path.
    prev_sys_path = list(sys.path) 

    site.addsitedir('/path/to/virtualenv/lib/python2.7/site-packages')

    # Reorder sys.path so new directories at the front.
    new_sys_path = [] 
    for item in list(sys.path): 
        if item not in prev_sys_path: 
            new_sys_path.append(item) 
            sys.path.remove(item) 
    sys.path[:0] = new_sys_path 

    from pyramid.paster import get_app
    from paste.script.util.logging_config import fileConfig
    fileConfig('/path/to/the/application/pyquest.ini')
    application = get_app('/path/to/the/application/pyquest.ini', 'main')


.. _WSGI: http://wsgi.readthedocs.org/en/latest/
.. _mod_wsgi: http://code.google.com/p/modwsgi/
.. _Apache2: http://httpd.apache.org/
.. _`pyramid deployment`: http://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/deployment/index.html