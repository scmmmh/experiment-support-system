import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'SQLAlchemy>=1.1.0',
    'alembic',
    'transaction',
    'pyramid_tm',
    'zope.sqlalchemy',
    'waitress',
    'kajiki',
    'babel',
    'decorator',
    'mimeparse',
    'formencode',
    'pyramid_beaker',
    'pycrypto',
    'asset',
    'pywebtools>=1.1.3',
    'compound_jsonapi>=1.0.0a1',
    'marshmallow>=3.0.0a0'
    ]

extra_requires = {
    'testing': [
        'tox',
        'pytest',
        'webtest',
        'flake8'
    ]
}

setup(name='ExperimentSupportSystem',
      version='1.0.0a16',
      description='Experiment Support System',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      install_requires = requires,
      extras_require = extra_requires,
      entry_points = """\
      [paste.app_factory]
      main = ess:main
      [console_scripts]
      ESS = ess.scripts.main:main
      """,
      )
