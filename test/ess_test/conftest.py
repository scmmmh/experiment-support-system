# -*- coding: utf-8 -*-
"""
###########################################
:mod:`ess_test.conftest` - Py.Test Fixtures
###########################################

This module provides a series of fixtures that can be used to have a fully configured
database session (:func:`~ess_test.conftest.database`) and :class:`~ess_test.conftest.DatabaseTester`
via the fixture :func:`~ess_test.conftest.database_tester`.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import json
import transaction
import pytest

from alembic import config, command
from pkg_resources import resource_string
from pyramid.paster import (get_app, get_appsettings, setup_logging)
from pywebtools.pyramid.auth.models import (User, PermissionGroup, Permission)
from pywebtools.sqlalchemy import (DBSession, Base)
from sqlalchemy import engine_from_config, text
from webtest import TestApp

from ess import models
from ess.importexport import load, QuestionTypeIOSchema

dbsession_initialised = False


@pytest.yield_fixture
def database():
    """The :func:`~ess_test.conftest.database` fixture initialises the database specified
    in the "testing.ini", removes any existing data, creates the standard permissions, and
    four test users:

    * admin - user with full administrative permissions
    * developer - user with full experiment development permissions
    * content - user with full editing permissions
    * general - user with no permissions
    """
    global dbsession_initialised

    # Load settings
    settings = get_appsettings('testing.ini')
    setup_logging('testing.ini')

    # Init the DB
    engine = engine_from_config(settings, 'sqlalchemy.')
    if not dbsession_initialised:
        DBSession.configure(bind=engine)
        dbsession_initialised = True
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    dbsession = DBSession()

    # Reset Database Content
    #with transaction.manager:
    #    tables = list(Base.metadata.sorted_tables)
    #    tables.reverse()
    #    for table in tables:
    #        dbsession.bind.execute(table.delete())
    #    dbsession.flush()

    # Create Test Users
    with transaction.manager:
        admin_user = User(email='admin@example.com', display_name='Admin', password='password')
        developer_user = User(email='developer@example.com', display_name='Developer', password='password')
        content_user = User(email='content@example.com', display_name='Content', password='password')
        general_user = User(email='general@example.com', display_name='General', password='password')
        dbsession.add(general_user)
        group = PermissionGroup(title='Site administrator')
        group.permissions.append(Permission(name='admin.users', title='Administer the users'))
        group.permissions.append(Permission(name='admin.groups', title='Administer the permission groups'))
        group.permissions.append(Permission(name='admin.question_types', title='Administer the question types'))
        admin_user.permission_groups.append(group)
        group = PermissionGroup(title='Developer')
        group.permissions.append(Permission(name='survey.new', title='Create new experiments'))
        admin_user.permission_groups.append(group)
        developer_user.permission_groups.append(group)
        group = PermissionGroup(title='Content administrator')
        group.permissions.append(Permission(name='survey.view-all', title='View all experiments'))
        group.permissions.append(Permission(name='survey.edit-all', title='Edit all experiments'))
        group.permissions.append(Permission(name='survey.delete-all', title='Delete all experiments'))
        content_user.permission_groups.append(group)
        dbsession.add(admin_user)
        dbsession.add(developer_user)
        dbsession.add(content_user)
        #question_types = load(QuestionTypeIOSchema(many=True),
        #                      json.loads(resource_string('ess',
        #                                                 'scripts/templates/default_question_types.json').\
        #    decode('utf-8')))
        #dbsession.add_all(question_types)

    # Alembic Stamp
    alembic_config = config.Config('testing.ini', ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'ess:migrations')
    command.stamp(alembic_config, "head")

    DBSession.remove()

    yield DBSession


class DBTester(object):
    """The :class:`~ess_test.conftest.DBTester` provides functionality for interacting with the
    database..
    """

    def __init__(self):
        self._dbsession = DBSession()

    def get_model(self, name, query_params = None):
        """Retrieve a single instance of the model ``name``, filtered by the ``query``.

        :param name: The name of the model to get the instance for
        :type name: ``unicode``
        :param query: The query to use for selecting the instance as a tuple of ``(field, comparator, value)``
        :type query: ``tuple``
        :return: The result of the query
        """
        cls = getattr(models, name)
        query = self._dbsession.query(cls)
        if query_params:
            if query_params[1] == '==':
                query = query.filter(getattr(cls, query_params[0]) == query_params[2])
        return query.first()

    def create_model(self, name, params):
        """Create a new instance of the model ``name`` with the given ``params``.

        :param name: The name of the model to create the instance of
        :type name: ``unicode``
        :param params: The initial parameters to use for creating the instance
        :type params: ``dict``
        :return: The new instance
        """
        cls = getattr(models, name)
        loaded = list(self._dbsession.identity_map.values())
        with transaction.manager:
            model = cls(**params)
            self._dbsession.add(model)
        self._dbsession.add(model)
        self._dbsession.add_all(loaded)
        return model

    def update(self, obj, **kwargs):
        """Update the given ``obj`` with the key/value parameters.

        :param obj: The obj to update
        :type obj: :class:`pywebtools.sqlalchemy.Base`
        """
        loaded = list(self._dbsession.identity_map.values())
        with transaction.manager:
            self._dbsession.add(obj)
            for key, value in kwargs.items():
                if isinstance(value, Base):
                    self._dbsession.add(value)
                setattr(obj, key, value)
        self._dbsession.add_all(loaded)

    def flush(self):
        """Flush the session."""
        self._dbsession.flush()

@pytest.yield_fixture
def database_tester(database):
    tester = DBTester()
    yield tester
