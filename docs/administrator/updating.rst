********
Updating
********

Preparation
===========

Before updating the Experiment Support System, perform the following three
steps to put the Experiment Support System into a state that is ready for the
update:

1. The first step is to download the latest "requirements.txt" from
   https://bitbucket.org/mhall/experiment-support-system/src.
2. Next stop the Experiment Support System application. How to do this depends
   on how you have deployed it (see :doc:`deployment`).
3. Finally, make a backup of the database. This will allow you to roll-back the
   application in case of there being any issues that arise during or after the
   update.

Core update
===========

To perform the actual update of the Experiment Support System, first activate
the `virtual environment`_ you previously installed the Experiment Support
System into. To install the new version you downloaded, run the following
command::

  pip install -r requirements.txt

This will install the downloaded version and also automatically install and
update any libraries the Experiment Support System depends on.

Next update the database to the latest schema by running::

  ESS update-database <configuration.ini>

You can then re-start the Experiment Support System and test that the update
has installed successfully.

.. _`virtual environment`: https://pypi.python.org/pypi/virtualenv
