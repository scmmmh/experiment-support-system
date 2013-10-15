#####
Setup
#####

The next step is to set up the Experiment Support System so that it is ready
to run. For this you need to:

1. Generate a configuratipn file
2. Initialise the database

Both tasks are done using the configuration application included in the
Experiment Support System. To see all options provided by the configuration application
run:

``ESS -h``

**************************
Generate the Configuration
**************************

To generate a configuration file run:

``ESS generate-config``

You will be asked to provide the `SQLAlchemy connection string`_ for your
database. If you don't know it yet, you can accept the default test database
and change the configuration setting later.

You can also set the following parameters on the commandline:

* --sqla-connection-string <SQL Alchemy connection string>
* --filename <Configuration Filename defaults to production.ini>

For details on the available configuration options, check :doc:`configuration`.

***********************
Initialise the Database
***********************

.. _SQLAlchemy connection string: docs.sqlalchemy.org/en/latest/dialects/