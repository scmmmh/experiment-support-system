*****
Setup
*****

The next step is to set up the Experiment Support System so that it is ready
to run. For this you need to:

1. Generate a configuration file
2. Initialise the database

Both tasks are done using the configuration application included in the
Experiment Support System. To see all options provided by the configuration application
run::

  ESS -h

Generate the Configuration
==========================

To generate the configuration file run::

  ESS generate-config

You will be asked to provide the `SQLAlchemy connection string`_ for your
database. If you don't know it yet, you can accept the default test database
and change the configuration setting later.

You can also set the following parameters on the commandline:

* --sqla-connection-string <SQL Alchemy connection string>
* --filename <Configuration Filename defaults to production.ini>

All further configuration is done via the generated configuration file.
Details of the available options is in the :doc:`configuration`
documentation.

Initialise the Database
=======================

After generating the configuration file, run::

  ESS initialise-database <configuration.ini>

to create the initial database structure. This will also create a default
administrative user with the following details::

  username: admin
  password: password

.. WARNING:: Make sure you change the password after logging in the first
   time!

The database initialisation can take an additional, optional parameter that
removes any tables from a previous installation of the Experiment Support
System. If you need this, then run::

  ESS initialise-database <configuration.ini> --drop-existing

Sample Data
-----------

The Experiment Support System comes with a set of sample experiments that
demonstrate some of the core functionality. To load these into the database
run::

  ESS load-sample-data <configuration.ini>

The sample experiments will be assigned to the first user in the database,
which by default will be the administrative user created as part of the
database initialisation.

After completing the application setup, continue either with the
:doc:`configuration` or :doc:`deployment` documentation.

.. _`SQLAlchemy connection string`: http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls
