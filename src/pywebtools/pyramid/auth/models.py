# -*- coding: utf-8 -*-
"""
#########################################################################
:mod:`pywebtools.pyramid.auth.models` -- Authentication SQLAlchemy Models
#########################################################################

This module contains all the SQLAlchemy models needed to implement
the persistence level of the authentication framework. The main classes of
interest are the :class:`~pywebtools.pyramid.auth.models.User` and
:class:`~pywebtools.pyramid.auth.models.TimeToken`.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import hashlib
import json
import random

from sqlalchemy import (Table, Column, Index, ForeignKey, Integer, Unicode,
                        DateTime, UnicodeText)
from sqlalchemy.orm import (relationship, reconstructor, backref)
from uuid import uuid4

from pywebtools.sqlalchemy import Base, DBSession


class User(Base):
    """The :class:`~pywebtools.pyramid.auth.models.User` represents a generic user. Which
    functionality they can access is determined purely through the individual
    :class:`~pywebtools.pyramid.auth.models.User`'s
    :class:`~pywebtools.pyramid.auth.models.Permission`.

    Instances of the :class:`~pywebtools.pyramid.auth.models.User` have the following attributes:

    * ``id`` -- The unique database identifier
    * ``display_name`` -- The name to display
    * ``email`` -- The e-mail address used for login and communication
    * ``login_limit`` -- Login limitation counter to stop brute-force login
      attacks
    * ``parts`` -- The :class:`~pywebtools.pyramid.auth.models.UserPartProgress` belonging to this
      :class:`~wte.modes.User`
    * ``password`` -- The hashed password
    * ``permissions`` -- The :class:`~pywebtools.pyramid.auth.models.User`'s list of
      :class:`~pywebtools.pyramid.auth.models.Permission`.
    * ``permission_groups`` -- The :class:`~pywebtools.pyramid.auth.models.User`'s list of
      :class:`~pywebtools.pyramid.auth.models.PermissionGroup`.
    * ``salt`` -- The password hash salt
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(Unicode(255), unique=True)
    salt = Column(Unicode(255))
    password = Column(Unicode(255))
    display_name = Column(Unicode(64))
    login_limit = Column(Integer)
    status = Column(Unicode(255))

    permissions = relationship('Permission', backref='users', secondary='users_permissions')
    permission_groups = relationship('PermissionGroup', backref='users', secondary='users_permission_groups')

    def __init__(self, **kwargs):
        """Constructs a new :class:`~pywebtools.pyramid.auth.models.User` with the given email
        address, display name, and optionally password.
        """
        Base.__init__(self, **kwargs)
        self.preferences_ = {}

    @reconstructor
    def init(self):
        self.preferences_ = {}

    def new_salt(self):
        """Generates a new :data:`~pywebtools.pyramid.auth.models.User.salt``. Will use
        ``os.urandom`` if available and the standard pseudo-random if not.
        """
        try:
            rng = random.SystemRandom()
            self.salt = ''.join(chr(rng.randint(32, 127)) for _ in range(32))
        except:
            self.salt = ''.join(chr(random.randint(32, 127)) for _ in range(32))

    def new_password(self, password):
        """Sets the given ``password`` as the :class:`~pywebtools.pyramid.auth.models.User`'s new
        password. Calls :func:`~pywebtools.pyramid.auth.models.User.new_salt` to generate a new
        salt for the password.

        :param password: The new cleartext password
        :type password: `unicode`
        """
        self.new_salt()
        self.password = str(hashlib.sha512(('%s$$%s' % (self.salt, password)).encode('utf-8')).hexdigest())

    def password_matches(self, password):
        """Checks whether the given password matches the hashed, stored
        password.

        :param password: The password to check
        :type password: `unicode`
        :return: ``True`` if the passwords match, ``False`` otherwise
        :rtype: `bool`
        """
        password = str(hashlib.sha512(('%s$$%s' % (self.salt, password)).encode('utf-8')).hexdigest())
        return password == self.password

    def has_permission(self, permission):
        """Checks whether the user has been granted the given ``permission``,
        either directly or via a :class:`~pywebtools.pyramid.auth.models.PermissionGroup`.

        :param permission: The permission to check for
        :type permission: `unicode`
        :return: ``True`` if the user has the permission, ``False`` otherwise
        :rtype: `bool`
        """
        if hasattr(self, '_permissions'):
            return permission in self._permissions
        else:
            dbsession = DBSession()
            direct_perm = dbsession.query(Permission.name).join(User, Permission.users).filter(User.id == self.id)
            group_perm = dbsession.query(Permission.name).join(PermissionGroup, Permission.permission_groups).\
                join(User, PermissionGroup.users).filter(User.id == self.id)
            self._permissions = [p[0] for p in direct_perm.union(group_perm)]
            return self.has_permission(permission)

    def allow(self, action, user):
        """Checks whether the given ``user`` is allowed to perform the given
        ``action``. Supports the following actions: view, edit, delete.

        :param action: The action to check for
        :type action: `unicode`
        :param user: The user to check
        :type user: :class:`~pywebtools.pyramid.auth.models.User`
        :return: ``True`` if the ``user`` may perform the action, ``False``
                 otherwise
        :rtype: `bool`
        """
        if action == 'view':
            if self.id == user.id:
                return True
            return True  # TODO: Add support for showing / hiding profile
        elif action == 'edit':
            if self.id == user.id:
                return True
            return user.has_permission('admin.users.edit')
        elif action == 'edit-permissions':
            return user.has_permission('admin.users.permissions')
        elif action == 'delete':
            if self.id == user.id:
                return True
            return user.has_permission('admin.users.delete')
        return False

Index('users_email_ix', User.email)


users_permissions = Table('users_permissions', Base.metadata,
                          Column('user_id',
                                 ForeignKey('users.id',
                                            name='users_permissions_users_fk'),
                                 primary_key=True),
                          Column('permission_id',
                                 ForeignKey('permissions.id',
                                            name='users_permissions_permissions_fk'),
                                 primary_key=True))
""":class:`sqlalchemy.Table` to link :class:`~pywebtools.pyramid.auth.models.User` and
:class:`~pywebtools.pyramid.auth.models.Permission`.
"""


class Permission(Base):
    """The :class:`~pywebtools.pyramid.auth.models.Permission` class represents a single
    permission that can be granted to a :class:`~pywebtools.pyramid.auth.models.User` or to a
    :class:`~pywebtools.pyramid.auth.models.PermissionGroup`.

    Instances of :class:`~pywebtools.pyramid.auth.models.Permission` have the following attributes:

    * ``id`` -- The unique database identifier
    * ``name`` -- The unique name used for permission checking
    * ``permission_groups`` -- List of :class:`~pywebtools.pyramid.auth.models.PermissionGroup`
      that contain this :class:`~pywebtools.pyramid.auth.models.Permission`
    * ``title`` -- The title displayed for this :class:`~pywebtools.pyramid.auth.models.Permission`
    * ``users`` -- List of :class:`~pywebtools.pyramid.auth.models.User` that have this
      :class:`~pywebtools.pyramid.auth.models.Permission`
    """

    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)
    title = Column(Unicode(255))

Index('permissions_name_ix', Permission.name)


class PermissionGroup(Base):
    """The :class:`~pywebtools.pyramid.auth.models.PermissionGroup` groups together one or more
    :class:`~pywebtools.pyramid.auth.models.Permission` for easier administration.

    Instances of :class:`~pywebtools.pyramid.auth.models.PermissionGroup` have the following
    attributes:

    * ``id`` -- The unique database identifier
    * ``permissions`` -- The list of grouped :class:`~pywebtools.pyramid.auth.models.Permission`
    * ``title`` -- The title displayed for this
      :class:`~pywebtools.pyramid.auth.models.PermissionGroup`
    * ``users`` -- List of :class:`~pywebtools.pyramid.auth.models.User` that have this
      :class:`~pywebtools.pyramid.auth.models.PermissionGroup`
    """
    __tablename__ = 'permission_groups'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255))

    permissions = relationship('Permission', backref='permission_groups', secondary='permission_groups_permissions')


groups_permissions = Table('permission_groups_permissions', Base.metadata,
                           Column('permission_group_id',
                                  ForeignKey(PermissionGroup.id,
                                             name='permission_groups_permissions_groups_fk'),
                                  primary_key=True),
                           Column('permission_id',
                                  ForeignKey(Permission.id,
                                             name='permission_groups_permissions_permissions_fk'),
                                  primary_key=True))
""":class:`sqlalchemy.Table` to link :class:`~pywebtools.pyramid.auth.models.PermissionGroup` and
:class:`~pywebtools.pyramid.auth.models.Permission`.
"""


users_groups = Table('users_permission_groups', Base.metadata,
                     Column('user_id', ForeignKey(User.id,
                                                  name='users_permission_groups_users_fk'),
                            primary_key=True),
                     Column('permission_group_id', ForeignKey(PermissionGroup.id,
                                                              name='users_permission_groups_groups_fk'),
                            primary_key=True))
""":class:`sqlalchemy.Table` to link :class:`~pywebtools.pyramid.auth.models.User` and
:class:`~pywebtools.pyramid.auth.models.PermissionGroup`.
"""


class TimeToken(Base):
    """The :class:`~pywebtools.pyramid.auth.models.TimeToken` represents a validation token that has
    a timeout period.

    Instances of the :class:`~pywebtools.pyramid.auth.models.TimeTokne` have the following attributes:

    * ``id`` -- The unique database identifier
    * ``user_id`` -- The identifier of the :class:`~pywebtools.pyramid.auth.models.User`` it belongs to
    * ``action`` -- The action the :class:`~pywebtools.pyramid.auth.models.TimeToken` is associated with
    * ``token`` -- The random token
    * ``timeout`` -- The timeout timestamp until which the :class:`~pywebtools.pyramid.auth.models.TimeToken` is valid
    * ``data`` -- Any payload data
    """
    __tablename__ = 'time_tokens'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id',
                                         name='time_tokens_user_id_fk'))
    action = Column(Unicode(255))
    token = Column(Unicode(255))
    timeout = Column(DateTime())
    data = Column(UnicodeText())

    user = relationship('User', backref=backref('time_tokens', cascade="all, delete-orphan"))

    def __init__(self, user_id, action, timeout, data=None):
        self.user_id = user_id
        self.action = action
        self.token = uuid4().hex
        self.timeout = timeout
        if data:
            self.data = json.dumps(data)


Index('time_tokens_full_ix', TimeToken.action, TimeToken.token, TimeToken.timeout)
