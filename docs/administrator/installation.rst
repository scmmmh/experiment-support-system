********************
Initial Installation
********************

It is generally recommended that PyQuestionnaire is installed into its own
``virtualenv`` (see `https://pypi.python.org/pypi/virtualenv`_).

Installing the Core Software
============================

It is recommended that you install the latest stable release, but if you wish
to contribute back to the project, please install the latest development version.

Stable releases
---------------

To install the latest stable release run:

``pip install pyquestionnaire``

To install an older release, download the release from
https://bitbucket.org/mhall/pyquestionnaire/downloads and then install using:

``pip install pyquestionnaire-x.y.z.tar.gz``

Source code
-----------

To install the latest development version from source, clone the Mercurial
repository:

``hg clone hg clone https://bitbucket.org/mhall/pyquestionnaire``

Additional Required Packages
============================

PyQuestionnaire additionally requires further packages to be fully operational:

* a cryptography library to support secure session cookies;
* a database access library.

Secure session handling
-----------------------

You need to install either *pycryptopp* or *PyCrypto* packages to enable
the use of secure session cookies:

``pip install pycryptopp``

or

Download PyCrypto from https://www.dlitz.net/software/pycrypto/ and install
using ``pip install pycrypto-X.Y.tar.gz``.

Database access
---------------

PyQuestionnaire uses `SQLAlchemy`_ as its database access library and thus in
theory supports any `database supported by SQLAlchemy`_. The following databases
have been tested with PyQuestionnaire:

PostgreSQL
    Recommended, fully supported and tested with the ``psycopg2`` database adapter:
    
    ``pip install psycopg2``

MySQL
    Fully supported and tested with the ``mysql-python`` database adapter:
    
    ``pip install mysql-python``

SQLite
    Only supported for testing purposes. SQLite does not support all DDL
    statements required to upgrade the database for future releases, thus it is
    not recommended to use it in a production environment.
    
All other databases
    Should in theory be supported, but have not been tested. If you have
    deployed PyQuestionnaire using another database backend, please let us know
    and the documentation will be updated.

After installing PyQuestionnaire and the required additional packages, you can move on to :doc:`setting it up <setup>`.

.. _SQLAlchemy: http://sqlalchemy.org
.. _database supported by SQLAlchemy: docs.sqlalchemy.org/en/latest/dialects/
.. _SQLite: http://www.sqlite.org/