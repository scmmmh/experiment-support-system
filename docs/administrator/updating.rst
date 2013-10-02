********
Updating
********

Updating the Experiment Support System is very simple:

1. Stop the Experiment Support System application
2. Create a backup of your database
3. Activate the Experiment Support System's virtualenv
4. Run

   ``pip install ExperimentSupportSystem``
   
   to install the latest version of the Experiment Support System. Alternatively you can
   download another release from https://bitbucket.org/mhall/pyquestionnaire/downloads
   and install that via
   
   ``pip install ExperimentSupportSystem-x.y.z.tar.gz``
5. Finally, update the database schema by running
   
   ``ESS update-database <Configuration File>``
6. Re-start the Experiment Support System application
