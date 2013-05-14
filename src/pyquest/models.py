# -*- coding: utf-8 -*-
import json
import random
import hashlib

from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey,
                        Table, DateTime, Boolean, func, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship, backref,
                            reconstructor)
from zope.sqlalchemy import ZopeTransactionExtension

from pyquest.helpers import as_data_type
from pyquest.util import convert_type

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

DB_VERSION = '40af42e8f394'

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
        self.preferences_ = {}
    
    @reconstructor
    def init(self):
        self.preferences_ = {}
        
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
    
    def preference(self, key, default=None, data_type=None):
        if not self.preferences_:
            for pref in self.preferences:
                self.preferences_[pref.key] = pref.value
        if key in self.preferences_:
            return as_data_type(self.preferences_[key], data_type)
        else:
            return default
    
users_permissions = Table('users_permissions', Base.metadata,
                          Column('user_id', ForeignKey('users.id'), primary_key=True),
                          Column('permission_id', ForeignKey('permissions.id'), primary_key=True))

class Permission(Base):
    
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), index=True, unique=True)
    title = Column(Unicode(255))
    
class Group(Base):
    
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255))
    
    permissions = relationship('Permission', backref='groups', secondary='groups_permissions')
    
groups_permissions = Table('groups_permissions', Base.metadata,
                           Column('group_id', ForeignKey(Group.id), primary_key=True),
                           Column('permission_id', ForeignKey(Permission.id), primary_key=True))

users_groups = Table('users_groups', Base.metadata,
                     Column('user_id', ForeignKey(User.id), primary_key=True),
                     Column('group_id', ForeignKey(Group.id), primary_key=True))

class Preference(Base):
    
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(User.id), index=True)
    key = Column(Unicode(255))
    value = Column(Unicode(255))
    
    user = relationship('User', backref='preferences')
    
class Survey(Base):

    __tablename__ = 'surveys'
    
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(1024))
    summary = Column(Unicode(4096))
    styles = Column(UnicodeText)
    scripts = Column(UnicodeText)
    status = Column(Unicode(64))
    start_id = Column(Integer, ForeignKey('qsheets.id', use_alter=True, name='fk_start_id'))
    language = Column(Unicode(64))
    owned_by = Column(ForeignKey(User.id))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime)
    
    owner = relationship('User', backref='surveys')
    qsheets = relationship('QSheet',
                           backref='survey',
                           primaryjoin='Survey.id==QSheet.survey_id',
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
    name = Column(Unicode(255))
    title = Column(Unicode(255))
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
    data_items = relationship('DataItem',
                             backref='qsheet',
                             order_by='DataItem.order',
                             cascade='all, delete, delete-orphan')
    
    def attr(self, key):
        for attr in self.attributes:
            if attr.key == key:
                return attr
        return None
    
    def attr_value(self, key, default=None):
        attr = self.attr(key)
        if attr:
            return attr.value
        else:
            return default
    
    def set_attr_value(self, key, value):
        attr = self.attr(key)
        if attr:
            attr.value = value
        else:
            self.attributes.append(QSheetAttribute(key=key, value=value))

class QSheetAttribute(Base):
    
    __tablename__ = 'qsheet_attributes'
    
    id = Column(Integer, primary_key=True)
    qsheet_id = Column(ForeignKey(QSheet.id))
    key = Column(Unicode(255))
    value = Column(UnicodeText)

class QuestionTypeGroup(Base):
    
    __tablename__ = 'question_type_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    order = Column(Integer)
    parent_id = Column(ForeignKey(id))
    enabled = Column(Boolean, default=True)

    parent = relationship('QuestionTypeGroup',
                          backref=backref('children', order_by='QuestionTypeGroup.order', cascade='all, delete-orphan'),
                          remote_side=[id])
    
class QuestionType(Base):
    
    __tablename__ = 'question_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    dbschema = Column(UnicodeText)
    answer_validation = Column(UnicodeText)
    backend = Column(UnicodeText)
    frontend = Column(UnicodeText)
    group_id = Column(ForeignKey(QuestionTypeGroup.id))
    parent_id = Column(ForeignKey(id))
    enabled = Column(Boolean, default=True)
    order = Column(Integer)
    
    q_type_group = relationship(QuestionTypeGroup, backref=backref('q_types', order_by='QuestionType.order', cascade='all, delete-orphan'))
    parent = relationship('QuestionType', backref='children', remote_side=[id])
    
    def backend_schema(self):
        if self.backend:
            return json.loads(self.backend)
        elif self.parent:
            return self.parent.backend_schema()
        else:
            return []
    
    def dbschema_schema(self):
        if self.dbschema:
            return json.loads(self.dbschema)
        elif self.parent:
            return self.parent.dbschema_schema()
        else:
            return []
    
    def answer_schema(self):
        if self.answer_validation:
            return json.loads(self.answer_validation)
        elif self.parent:
            return self.parent.answer_schema()
        else:
            return []
    
    def frontend_doc(self):
        if self.frontend:
            return self.frontend
        elif self.parent:
            return self.parent.frontend_doc()
        else:
            return ''            

class Question(Base):
    
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    qsheet_id = Column(ForeignKey(QSheet.id))
    type_id = Column(ForeignKey(QuestionType.id))
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    required = Column(Boolean)
    help = Column(Unicode(255))
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
    q_type = relationship('QuestionType', backref='questions')
    
    def attr_group(self, path, default=None, multi=False):
        values = []
        for group in self.attributes:
            if group.key == path:
                if multi:
                    values.append(group)
                else:
                    return group
        if values:
            return values
        else:
            return default
    
    def attr(self, path, multi=False):
        (q_group, q_attr) = path.split('.')
        values = []
        for group in self.attributes:
            if group.key == q_group:
                for attribute in group.attributes:
                    if attribute.key == q_attr:
                        if multi:
                            values.append(attribute)
                        else:
                            return attribute
        if values:
            return values
        else:
            return None
        
    def attr_value(self, path, default=None, multi=False, data_type=None):
        attr = self.attr(path, multi)
        if attr:
            if isinstance(attr, list):
                if data_type:
                    return [convert_type(a.value, target_type=data_type, default=default) for a in attr]
                else:
                    return [a.value if a.value else default for a in attr]
            else:
                if data_type:
                    return convert_type(attr.value, target_type=data_type, default=default)
                else:
                    if attr.value:
                        return attr.value
                    else:
                        return default
        else:
            return default
    
    def set_attr_value(self, path, value, order=0, group_order=0):
        attr = self.attr(path, multi=isinstance(value, list))
        if attr:
            attr.value = value # TODO: Fix updating of list values
        else:
            (q_group, q_attr) = path.split('.')
            attr_group = self.attr_group(q_group)
            if attr_group:
                if isinstance(value, list):
                    for idx, sub_value in enumerate(value):
                        attr_group.attributes.append(QuestionAttribute(key=q_attr, value=sub_value, order=order + idx))
                else:
                    attr_group.attributes.append(QuestionAttribute(key=q_attr, value=value, order=order))
            else:
                attr_group = QuestionAttributeGroup(key=q_group, order=group_order)
                self.attributes.append(attr_group)
                if isinstance(value, list):
                    for idx, sub_value in enumerate(value):
                        attr_group.attributes.append(QuestionAttribute(key=q_attr, value=sub_value, order=order + idx))
                else:
                    attr_group.attributes.append(QuestionAttribute(key=q_attr, value=value, order=order))

class QuestionAttributeGroup(Base):
    
    __tablename__ = 'question_complex_attributes'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(ForeignKey(Question.id))
    key = Column(Unicode(255))
    label = Column(Unicode(255))
    order = Column(Integer)
    
    attributes = relationship('QuestionAttribute',
                              backref='attribute_group',
                              order_by='QuestionAttribute.order',
                              cascade='all, delete, delete-orphan')
    
    def attr(self, path, multi=False):
        values = []
        for attr in self.attributes:
            if attr.key == path:
                if multi:
                    values.append(attr)
                else:
                    return attr
        if values:
            return values
        else:
            return None
        
    def attr_value(self, path, default=None, multi=False):
        attr = self.attr(path, multi)
        if attr:
            if isinstance(attr, list):
                return [a.value for a in attr]
            else:
                return attr.value
        else:
            return default
    
    def set_attr_value(self, path, value):
        attr = self.attr(path, False)
        if attr:
            attr.value = value
        else:
            self.attributes.append(QuestionAttribute(key=path, value=value, order=len(self.attributes) + 1))

class QuestionAttribute(Base):
    
    __tablename__ = 'question_attributes'
    
    id = Column(Integer, primary_key=True)
    question_group_id = Column(ForeignKey(QuestionAttributeGroup.id))
    key = Column(Unicode(255))
    label = Column(Unicode(255))
    value = Column(UnicodeText)
    order = Column(Integer)

class QSheetTransition(Base):
    
    __tablename__ = 'qsheet_transitions'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(QSheet.id))
    target_id = Column(ForeignKey(QSheet.id))

class TransitionCondition(Base):

    __tablename__ = 'transition_conditions'

    id = Column(Integer, primary_key=True)
    transition_id = Column(ForeignKey(QSheetTransition.id))
    question_id = Column(ForeignKey(Question.id))
    expected_answer = Column(Unicode(255))
    subquestion_name = Column(Unicode(255))

    transition = relationship("QSheetTransition", backref=backref('condition', uselist=False, cascade='all,delete-orphan'))

    def evaluate(self, dbsession, participant):
        """ Checks whether this TransitionCondition has been fulfilled. If the question is a sub-question then it looks only for the 
        relevant answer value. If the question has several answers but these are not specified as sub-questions (for example a multi-
        choice question) these are joined together in a single string for testing. 
        
        :param self: the TranstionCondition
        :param dbsession: a sqlalchemy data base session
        :param participant: a participant 
        :return True if the condition is fulfilled, False if not
        """
        question_id = self.question_id
        answer = dbsession.query(Answer).filter(Answer.question_id==question_id).filter(Answer.participant_id==participant.id).first()
        actual_answer = ''
        if (answer):
            query = dbsession.query(AnswerValue).filter(AnswerValue.answer_id==answer.id)
            if self.subquestion_name:
                answer_value = query.filter(AnswerValue.name==self.subquestion_name).first()
                actual_answer = answer_value.value
            else:
                answer_values = query.all()
                if len(answer_values) == 1:
                    actual_answer = answer_values[0].value
                else:
                    for av in answer_values:
                        actual_answer = actual_answer + av.value + ',' 
                    actual_answer = actual_answer[:-1]

        return eval('actual_answer =="' + self.expected_answer + '"')

class DataItemSet(Base):

    __tablename__ = 'data_item_sets'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    owned_by = Column(ForeignKey(User.id))
    qsheet_id = Column(Integer, ForeignKey(QSheet.id))

    items = relationship('DataItem', backref='item_set')
    qsheet = relationship('QSheet', backref=backref('dataset', uselist=False))
    owner = relationship('User', backref='datasets')

    def is_owned_by(self, user):
        if user:
            return self.owned_by == user.id
        else:
            return False
    
class DataItem(Base):
    
    __tablename__ = 'data_items'
    
    id = Column(Integer, primary_key=True)
    qsheet_id = Column(ForeignKey(QSheet.id))
    data_item_set_id = Column(ForeignKey(DataItemSet.id))
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
    key = Column(Unicode(255))
    value = Column(Unicode(255))

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
    answer = Column(Unicode(4096))

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
    name = Column(Unicode(255))
    value = Column(Unicode(4096))
