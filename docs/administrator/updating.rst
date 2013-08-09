********
Updating
********

Updating PyQuestionnaire is very simple:

1. Stop the PyQuestionnaire application
2. Create a backup of your database
3. Activate PyQuestionnaire's virtualenv
4. Run

   ``pip install --upgrade pyquestionnaire``
   
   to install the latest version of PyQuestionnaire. Alternatively you can
   download another release from https://bitbucket.org/mhall/pyquestionnaire/downloads
   and install that via
   
   ``pip install pyquestionnaire-x.y.z.tar.gz``
5. Finally, update the database schema by running
   
   ``PyQuestionnaire update-database <Configuration File>``
6. Re-start the PyQuestionnaire application
