*****
Setup
*****

The next step is to set up PyQuestionnaire so that it is ready to run. For this
you need to:

1. Generate a configuratipn file
2. Initialise the database

Both tasks are done using the configuration application included in
PyQuestionnaire. To see all options provided by the configuration application
run:

``PyQuestionnaire -h``

Generate the Configuration
==========================

To generate a configuration file run:

``PyQuestionnaire generate-config``

You will be asked to provide the `SQLAlchemy connection string`_ for your
database. If you don't know it yet, you can accept the default test database
and change the configuration setting later.

You can also set the following parameters on the commandline:

* --sqla-connection-string <SQL Alchemy connection string>
* --filename <Configuration Filename defaults to production.ini>

For details on the available configuration options, check the
:doc:`configuration <configuration>` documentation.

Initialise the Database
=======================

The final setup step is to initialise the database. If you did not specify the
`SQLAlchemy connection string`_ when generating the configuration, then
consult the :doc:`configuration` document on how to specify your connection
string. Then run:

``PyQuestionnaire initialise-database <Configuration File>``

and the required database tables will be created. During testing you might want
to re-create the initial database. In that case run:

``PyQuestionnaire initialise-database <Configuration File> --drop-existing``

and the old tables will be removed and the database re-created in its initial
state.

This command will also create an initial user::

    username: admin
    password: password

which you can then use to log in to PyQuestionnaire.

**CHANGE THESE IMMEDIATELY AFTER LOGGING IN FOR THE FIRST TIME!**

Sample data
===========

PyQuestionnaire comes with sample data demonstrating the various functionalities
provided by the software. To install this data, first initialise the database as
described above, and then run:

``PyQuestionnaire load-sample-data <Configuration File>``

The samples are accessible via the initial user created when initialising the
database.

.. _SQLAlchemy connection string: docs.sqlalchemy.org/en/latest/dialects/