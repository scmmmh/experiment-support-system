# -*- coding: utf-8 -*-
import random
import hashlib

from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey,
                        Table, DateTime, Boolean, func, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship, backref)
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

DB_VERSION = '2ad62f615ca'

class DBUpgradeException(Exception):
    
    def __init__(self, current, required):
        self.current = current
        self.required = required
    
    def __repr__(self):
        return "DBUpgradeException('%s', '%s'" % (self.current, self.required)
    
    def __str__(self):
        return """A database upgrade is required.

You are currently running version '%s', but version '%s' is required. Please run
alembic -c config.ini upgrade to upgrade the database and then start the application
again.
""" % (self.current, self.required)
    
def check_database_version():
    dbsession = DBSession()
    try:
        result = dbsession.query('version_num').\
                from_statement('SELECT version_num FROM alembic_version WHERE version_num = :version_num').\
                params(version_num=DB_VERSION).first()
        if not result:
            result = dbsession.query('version_num').from_statement('SELECT version_num FROM alembic_version').first()
            raise DBUpgradeException(result[0], DB_VERSION)
    except OperationalError:
            raise DBUpgradeException('no version-information found', DB_VERSION)

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
    name = Column(Unicode(255), index=True, unique=True)
    title = Column(Unicode)
    
class Group(Base):
    
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    
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
    styles = Column(UnicodeText)
    scripts = Column(UnicodeText)
    status = Column(Unicode)
    start_id = Column(Integer, ForeignKey('qsheets.id', use_alter=True, name='fk_start_id'))
    language = Column(Unicode)
    owned_by = Column(ForeignKey(User.id), default=func.now())
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    owner = relationship('User', backref='surveys')
    qsheets = relationship('QSheet',
                           backref='survey',
                           primaryjoin='Survey.id==QSheet.survey_id',
                           cascade='all, delete, delete-orphan')
    data_items = relationship('DataItem',
                             backref='survey',
                             order_by='DataItem.order',
                             cascade='all, delete, delete-orphan')
    participants = relationship('Participant',
                                backref='survey',
                                cascade='all, delete, delete-orphan')
    start = relationship('QSheet',
                         primaryjoin='Survey.start_id==QSheet.id',
                         post_update=True)
    
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
    styles = Column(UnicodeText)
    scripts = Column(UnicodeText)
    
    questions = relationship('Question',
                             backref='qsheet',
                             order_by='Question.order',
                             cascade='all, delete, delete-orphan')
    attributes = relationship('QSheetAttribute',
                              backref='qsheet',
                              cascade='all, delete, delete-orphan')
    next = relationship('QSheetTransition',
                        backref='source',
                        primaryjoin='QSheet.id==QSheetTransition.source_id',
                        cascade='all, delete, delete-orphan')
    prev = relationship('QSheetTransition',
                        backref='target',
                        primaryjoin='QSheet.id==QSheetTransition.target_id',
                        cascade='all, delete, delete-orphan')

class QSheetAttribute(Base):
    
    __tablename__ = 'qsheet_attributes'
    
    id = Column(Integer, primary_key=True)
    qsheet_id = Column(ForeignKey(QSheet.id))
    key = Column(Unicode)
    value = Column(Unicode)

class Question(Base):
    
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    qsheet_id = Column(ForeignKey(QSheet.id))
    type = Column(Unicode)
    name = Column(Unicode)
    title = Column(Unicode)
    required = Column(Boolean)
    help = Column(Unicode)
    order = Column(Integer)
    
    attributes = relationship('QuestionAttributeGroup',
                              backref='question',
                              order_by='QuestionAttributeGroup.order',
                              cascade='all, delete, delete-orphan')
    answers = relationship('Answer',
                           backref='question',
                           cascade='all, delete, delete-orphan')
    control_answers = relationship('DataItemControlAnswer',
                                   backref='question',
                                   cascade='all, delete, delete-orphan')

class QuestionAttributeGroup(Base):
    
    __tablename__ = 'question_complex_attributes'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(ForeignKey(Question.id))
    key = Column(Unicode)
    label = Column(Unicode)
    order = Column(Integer)
    
    attributes = relationship('QuestionAttribute',
                              backref='question',
                              order_by='QuestionAttribute.order',
                              cascade='all, delete, delete-orphan')

class QuestionAttribute(Base):
    
    __tablename__ = 'question_attributes'
    
    id = Column(Integer, primary_key=True)
    question_group_id = Column(ForeignKey(QuestionAttributeGroup.id))
    key = Column(Unicode)
    label = Column(Unicode)
    value = Column(Unicode)
    order = Column(Integer)

class QSheetTransition(Base):
    
    __tablename__ = 'qsheet_transitions'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(QSheet.id))
    target_id = Column(ForeignKey(QSheet.id))

class DataItem(Base):
    
    __tablename__ = 'data_items'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Survey.id))
    order = Column(Integer)
    control = Column(Boolean, default=False)
    
    attributes = relationship('DataItemAttribute',
                              backref='data_item', order_by='DataItemAttribute.order',
                              cascade='all, delete, delete-orphan')
    counts = relationship('DataItemCount',
                          backref='counts',
                          cascade='all, delete, delete-orphan')
    answers = relationship('Answer',
                           backref='data_item',
                           cascade='all, delete, delete-orphan')
    control_answers = relationship('DataItemControlAnswer',
                                   backref='data_item',
                                   cascade='all, delete, delete-orphan')

class DataItemAttribute(Base):
    
    __tablename__ = 'data_item_attributes'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id))
    order = Column(Integer)
    key = Column(Unicode)
    value = Column(Unicode)

class DataItemCount(Base):
    
    __tablename__ = 'data_item_counts'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id))
    qsheet_id = Column(ForeignKey(QSheet.id))
    count = Column(Integer)

class DataItemControlAnswer(Base):
    
    __tablename__ = 'data_item_control_answers'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id))
    question_id = Column(ForeignKey(Question.id))
    answer = Column(Unicode)
    
class Participant(Base):
    
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Survey.id))
    
    answers = relationship('Answer',
                           backref='participant',
                           cascade='all, delete, delete-orphan')

class Answer(Base):
    
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column(ForeignKey(Participant.id))
    question_id = Column(ForeignKey(Question.id))
    data_item_id = Column(ForeignKey(DataItem.id))
    
    values = relationship('AnswerValue',
                          backref='answer',
                          cascade='all, delete, delete-orphan')
    
class AnswerValue(Base):
    
    __tablename__ = 'answer_values'
    
    id = Column(Integer, primary_key=True)
    answer_id = Column(ForeignKey(Answer.id))
    name = Column(Unicode)
    value = Column(Unicode)
        