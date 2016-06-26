# -*- coding: utf-8 -*-
"""
#################################################################
:mod:`pywebtools.sqlalchemy` -- Utilities for use with SQLAlchemy
#################################################################

This module provide the generic ``DBSession`` :class:`~sqlalchemy.orm.scoped_session`
for use with Pyramid & SQLAlchemy. It also provides the ``Base``
:func:`~sqlalchemy.ext.declarative.declarative_base` that acts as the base class
for any declarative model. If you are starting from a SQLAlchemy + Pyramid starter
template in your ``models`` module, remove the ``DBSession`` and ``Base`` and
replace them imports from this module. Then do the same for the ``main`` function
in the main package.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import json

from sqlalchemy import (text, UnicodeText)
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import (scoped_session, sessionmaker)
from sqlalchemy.types import TypeDecorator
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class DBUpgradeException(Exception):
    """The :class:`~pywebtools.sqlalchemy.DBUpgradeException` is used to indicate that
    the database requires an upgrade before the Web Teaching Environment system
    can be used.
    """
    def __init__(self, current, required):
        self.current = current
        self.required = required

    def __repr__(self):
        return "DBUpgradeException('%s', '%s'" % (self.current, self.required)

    def __str__(self):
        return "A database upgrade is required.\n\n" + \
            "You are currently running version '%s', but version '%s' is " % (self.current, self.required) + \
            " required. Please run WTE update-database config.ini upgrade to upgrade the database " + \
            "and then start the application again."


def check_database_version(db_version):
    """Checks that the current version of the database matches the version specified
    by ``db_version``. This requires the use of the Alembic database migration library.

    :param db_version: The version identifier to check.
    :type db_version: ``str``
    """
    dbsession = DBSession()
    try:
        inspector = Inspector.from_engine(dbsession.bind)
        if 'alembic_version' in inspector.get_table_names():
            result = dbsession.query('version_num').\
                from_statement(text('SELECT version_num FROM alembic_version WHERE version_num = :version_num')).\
                params(version_num=db_version).first()
            if not result:
                result = dbsession.query('version_num').\
                    from_statement('SELECT version_num FROM alembic_version').first()
                raise DBUpgradeException(result[0], db_version)
    except OperationalError:
        raise DBUpgradeException('No version-information found', db_version)


class JSONUnicodeText(TypeDecorator):
    """The class:`~pywebtools.sqlalchemy.JSONUnicodeText` is an extension to the
    :class:`~sqlalchemy.UnicodeText` column type that does automatic conversion
    from the JSON string representation stored in the DB to a dict/list representation
    for use in python.
    """

    impl = UnicodeText

    def process_bind_param(self, value, dialect):
        """Convert the dict/list to JSON for storing.
        """
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Convert the JSON to dict/list for use.
        """
        if value is not None:
            value = json.loads(value)
        return value


class MutableDict(Mutable, dict):
    """The :class:`~pywebtools.sqlalchemy.MutableDict` is a ``dict`` extension for use
    with the :class:`~pywebtools.sqlalchemy.JSONUnicodeText` column. It monitors any
    change to its values and marks the column as dirty, if a change has occurred.

    It is smart about its internal structure and will convert any nested ``dict`` into
    :class:`~pywebtools.sqlalchemy.MutableDict` as well, to ensure that all changes
    are tracked.
    """

    def __init__(self, *args, **kwargs):
        """Initialise the :class:`~pywebtools.sqlalchemy.MutableDict` and convert any nested
        ``dict`` to :class:`~pywebtools.sqlalchemy.MutableDict`.

        :params __notify: Optional :class:`~pywebtools.sqlalchemy.MutableDict` to notify
                          on changes. Needed for nested :class:`~pywebtools.sqlalchemy.MutableDict`.
        :type __notify: :class:`~pywebtools.sqlalchemy.MutableDict`
        """
        if '__notify' in kwargs:
            self.__notify = kwargs['__notify']
            del kwargs['__notify']
        else:
            self.__notify = self
        dict.__init__(self, *args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                dict.__setitem__(self, k, MutableDict(v, __notify=self))

    @classmethod
    def coerce(cls, key, value):
        """Automatically coerce any ``dict`` to a :class:`~pywebtools.sqlalchemy.MutableDict`. Used
        by SQLAlchemy.
        """
        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        """Set an key's value and mark as dirty.
        """
        dict.__setitem__(self, key, value)
        self.__notify.changed()

    def __delitem__(self, key):
        """Delete a key and mark as dirty.
        """
        dict.__delitem__(self, key)
        self.__notify.changed()
