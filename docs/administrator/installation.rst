************
Installation
************

Core System
===========

To install the Experiment Support System, download the latest version from
https://bitbucket.org/mhall/experiment-support-system and install using the
following command::

  pip install ExperimentSupportSystem-x.y.z.tar.gz

It is recommended that you install the Experiment Support System into a
`virtual environment`_.

To enable the Experiment Support System to work, you must then install either
`pycryptopp`_ or `PyCrypto`_ packages to enable the use of session cookies. To
install `pycryptopp`_ run::

  pip install pycryptopp

To install `PyCrypto`_, download it from https://www.dlitz.net/software/pycrypto/
and then install using the following command::

  pip install pycrypto-X.Y.tar.gz

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
.. _`pycryptopp`: 
.. _`PyCrypto`: https://www.dlitz.net/software/pycrypto/
.. _`PostgreSQL`: http://www.postgresql.org/
.. _`MySQL`: http://www.mysql.com/
.. _`SQLite`: http://www.sqlite.org/
.. _`Other database systems`: http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html#supported-databases
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
