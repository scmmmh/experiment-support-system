# -*- coding: utf-8 -*-
import random
import hashlib

from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey,
                        Table, DateTime, Boolean, func, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship)
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class User(Base):
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(Unicode(64), unique=True, index=True)
    email = Column(Unicode(255))
    salt = Column(Unicode(255))
    password = Column(Unicode(255))
    display_name = Column(Unicode(64))
    login_limit = Column(Integer)
    
    permissions = relationship('Permission', backref='users', secondary='users_permissions')
    groups = relationship('Group', backref='users', secondary='users_groups')
    
    def __init__(self, username, email, display_name, password=None):
        self.username = username
        self.email = email
        self.display_name = display_name
        self.salt = u''.join(unichr(random.randint(0, 127)) for _ in range(32))
        if password:
            self.password = unicode(hashlib.sha512('%s$$%s' % (self.salt, password)).hexdigest())
        else:
            self.password = u''
        self.login_limit = 0
    
    def new_password(self, password):
        self.salt = u''.join(unichr(random.randint(0, 127)) for _ in range(32))
        self.password = unicode(hashlib.sha512('%s$$%s' % (self.salt, password)).hexdigest())
    
    def password_matches(self, password):
        password = unicode(hashlib.sha512('%s$$%s' % (self.salt, password)).hexdigest())
        return password == self.password
    
    def has_permission(self, permission):
        dbsession = DBSession()
        direct_perm = dbsession.query(Permission.name).join(User, Permission.users).filter(User.id==self.id)
        group_perm = dbsession.query(Permission.name).join(Group, Permission.groups).join(User, Group.users).filter(User.id==self.id)
        return permission in map(lambda p: p[0], direct_perm.union(group_perm))
    
users_permissions = Table('users_permissions', Base.metadata,
                          Column('user_id', ForeignKey('users.id'), primary_key=True),
                          Column('permission_id', ForeignKey('permissions.id'), primary_key=True))

class Permission(Base):
    
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), index=True)
    
class Group(Base):
    
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), index=True)
    
    permissions = relationship('Permission', backref='groups', secondary='groups_permissions')
    
groups_permissions = Table('groups_permissions', Base.metadata,
                           Column('group_id', ForeignKey(Group.id), primary_key=True),
                           Column('permission_id', ForeignKey(Permission.id), primary_key=True))

users_groups = Table('users_groups', Base.metadata,
                     Column('user_id', ForeignKey(User.id), primary_key=True),
                     Column('group_id', ForeignKey(Group.id), primary_key=True))

class Survey(Base):

    __tablename__ = 'surveys'
    
    id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    summary = Column(Unicode)
    content = Column(UnicodeText)
    schema = Column(Text)
    status = Column(Unicode)
    owned_by = Column(ForeignKey(User.id), default=func.now())
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    owner = relationship('User', backref='surveys')
    qsheets = relationship('QSheet',
                           backref='survey',
                           cascade='all, delete, delete-orphan')
    data_items = relationship('DataItem',
                             backref='survey',
                             order_by='DataItem.order',
                             cascade='all, delete, delete-orphan')
    participants = relationship('Participant',
                                backref='survey',
                                cascade='all, delete, delete-orphan')
    
    def is_owned_by(self, user):
        if user:
            return self.owned_by == user.id
        else:
            return False

class QSheet(Base):
    
    __tablename__ = 'qsheets'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Survey.id))
    name = Column(Unicode)
    title = Column(Unicode)
    content = Column(UnicodeText)
    schema = Column(Text)
    
class DataItem(Base):
    
    __tablename__ = 'data_items'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Survey.id))
    order = Column(Integer)
    
    attributes = relationship('DataItemAttribute',
                              backref='data_item', order_by='DataItemAttribute.order',
                              cascade='all, delete, delete-orphan')

class DataItemAttribute(Base):
    
    __tablename__ = 'data_item_attributes'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id))
    order = Column(Integer)
    key = Column(Unicode)
    value = Column(Unicode)
    answer = Column(Unicode, nullable=True)

class Participant(Base):
    
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Survey.id))
    answers = Column(Text)
    