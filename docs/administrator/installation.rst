************
Installation
************

Core System
===========

To install the Experiment Support System, download the "requirements.txt" from
https://bitbucket.org/mhall/experiment-support-system/src and install using the
following command::

  pip install -r requirements.txt

It is recommended that you install the Experiment Support System into a
`virtual environment`_ that has been set up with python 3.

Database Access
===============

You will also need to install database access libraries for the database you
intend to use. The Experiment Support System has been tested with `PostgreSQL`_
and `MySQL`_. `SQLite`_ is not supported, as it does not provide the features
required to migrate the database when the Experiment Support System is upgraded.
`Other database systems`_ that are supported by `SQLAlchemy`_ can be used, but
have not been tested.

To use PostgreSQL as the database, run::

  pip install psycopg2

For MySQL run::

  pip install mysql-python

After the installation has completed, move on to the :doc:`setup`.

.. _`virtual environment`: https://pypi.python.org/pypi/virtualenv
.. _`PostgreSQL`: http://www.postgresql.org/
.. _`MySQL`: http://www.mysql.com/
.. _`SQLite`: http://www.sqlite.org/
.. _`Other database systems`: http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html#supported-databases
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
