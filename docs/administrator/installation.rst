Installation
============

``pip install pyquestionnaire-x.y.z.tar.gz``

It is recommended that you install PyQuestionnaire into a virtual
environment.

You then need to install either *pycryptopp* or *PyCrypto* packages to enable
the use of session cookies:

``pip install pycryptopp``

or

Download PyCrypto from https://www.dlitz.net/software/pycrypto/ and install
using ``pip install pycrypto-X.Y.tar.gz``.

You will also need to download database libraries for the database you intend
to use. For PostgreSQL ``pip install psycopg2``, for MySQL ``pip install mysql-python``.
SQLite is not supported, because it does not provide all required features for
smoothly migrating the database.

After the installation has completed, run ``populate_PyQuestionnaire pyquest.ini``.

You can then start the application by running ``pserve pyquest.ini``.
