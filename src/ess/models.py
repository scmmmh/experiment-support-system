# -*- coding: utf-8 -*-
"""
:mod:`pyquest.models`
=============================

This module contains all the database-abstraction classes.

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json
import random
import hashlib
import time

from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey,
                        Table, DateTime, Boolean, func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship, backref,
                            reconstructor)
from zope.sqlalchemy import ZopeTransactionExtension
from uuid import uuid1

from pyquest.helpers import as_data_type
from pyquest.util import convert_type

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


DB_VERSION = '5a464c95c7f1'
"""The currently required database version."""


class DBUpgradeException(Exception):
    """The :class:`~pyquest.models.DBUpgradeException` is used to indicate that
    the database requires an upgrade before the Experiment Support System system
    can be used.
    """
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
    """Checks that the current version of the database matches the version specified
    by :data:`~ess.models.DB_VERSION`.
    """
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


class AttributesMixin(object):
    """The :class:`~ess.models.AttributesMixin` adds an ``attributes`` column to the object
    it is mixed into. Additionally it provides the necessary functions so that the object
    it is mixed into acts as a dictionary, which is backed by JSON encoded data in the
    ``attributes`` column.

    The :class:`~ess.models.AttributesMixin` also supports a parent lookup. By specifying
    the ``__parent_attr_`` attribute with the name of an attribute that points to another
    instance that mixes in :class:`~ess.models.AttributesMixin`, the :class:`~ess.models.AttributesMixin`
    will look for any attribute that is not found in the current instance in the parent
    instance. However, setting an attribute will always apply to the current instance's
    stored attributes.
    """

    attributes = Column(UnicodeText)


    def __contains__(self, key):
        """Checks whether the given key exists in the object's attributes. If ``__parent_attr__``
        is specified, will check in that property if the key does not exist in the current
        object's attributes."""
        if key in self._attributes:
            return True
        else:
            if hasattr(self, '__parent_attr__') and getattr(self, self.__parent_attr__) is not None:
                return key in getattr(self, self.__parent_attr__)
            else:
                return False

    def __getitem__(self, key):
        """Retrieves the stored value for the given key, if it exists in the object's attributes.
        If ``__parent_attr__`` is specified, will retrieve the attribute value from that property.
        Unlike standard dictionaries, this will return None, if no value exists for the key, rather
        than throw an error."""
        if key in self._attributes:
            return self._attributes[key]
        elif hasattr(self, '__parent_attr__') and getattr(self, self.__parent_attr__) is not None:
            return getattr(self, self.__parent_attr__)[key]
        else:
            return None

    def __setitem__(self, key, value):
        """Sets the attribute ``key`` to the given ``value`` and updates the backing JSON database
        property."""
        self._attributes[key] = value
        self.attributes = json.dumps(self._attributes)

    @property
    def _attributes(self):
        """Helper function that handles caching of the backing JSON database property. Should only
        be used inside the :class:`~ess.models.AttributesMixin`. External access should directly
        use the in/get/set functionality of the object itself.
        """
        if hasattr(self, '_cached_attributes'):
            return self._cached_attributes
        else:
            if self.attributes:
                self._cached_attributes = json.loads(self.attributes)
            else:
                self._cached_attributes = {}
            return self._attributes


class User(Base):
    """The :class:`~pyquest.models.User` represents the researcher who creates
    the experiment via a :class:`~pyquest.models.Experiment`. The participant in
    the experiment is represented by :class:`~pyquest.models.Participant`.
    """
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
                          Column('user_id', ForeignKey('users.id', name='users_permissions_users_fk'), primary_key=True),
                          Column('permission_id', ForeignKey('permissions.id', name='users_permissions_permissions_fk'), primary_key=True))

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
                           Column('group_id', ForeignKey(Group.id, name='groups_permissions_groups_fk'), primary_key=True),
                           Column('permission_id', ForeignKey(Permission.id, 'groups_permissions_permissions_fk'), primary_key=True))

users_groups = Table('users_groups', Base.metadata,
                     Column('user_id', ForeignKey(User.id, name='users_groups_users_fk'), primary_key=True),
                     Column('group_id', ForeignKey(Group.id, name='users_groups_groups_fk'), primary_key=True))

class Preference(Base):
    
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(User.id, name='user_preferences_users_fk'), index=True)
    key = Column(Unicode(255))
    value = Column(Unicode(255))
    
    user = relationship('User', backref='preferences')
    
class Experiment(Base):

    __tablename__ = 'surveys'
    
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(1024))
    summary = Column(Unicode(4096))
    styles = Column(UnicodeText)
    scripts = Column(UnicodeText)
    status = Column(Unicode(64))
    start_id = Column(Integer, ForeignKey('qsheets.id', use_alter=True, name='fk_start_id'))
    language = Column(Unicode(64))
    external_id = Column(Unicode(64), index=True)
    owned_by = Column(ForeignKey(User.id, name='surveys_users_owner_fk'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime)
    public = Column(Boolean, default=True)

    owner = relationship('User', backref='surveys')
    qsheets = relationship('QSheet',
                           backref='survey',
                           primaryjoin='Experiment.id==QSheet.survey_id',
                           cascade='all, delete, delete-orphan')
    participants = relationship('Participant',
                                backref='survey',
                                cascade='all, delete, delete-orphan')
    start = relationship('QSheet',
                         primaryjoin='Experiment.start_id==QSheet.id',
                         post_update=True)

    notifications = relationship('Notification',
                          backref='survey',
                          cascade='all, delete, delete-orphan')
    
    data_sets = relationship('DataSet', 
                             primaryjoin="and_(Experiment.id==DataSet.survey_id, DataSet.type=='dataset')",
                             cascade='all, delete, delete-orphan')

    permutation_sets = relationship('PermutationSet', 
                                    primaryjoin="and_(Experiment.id==PermutationSet.survey_id, PermutationSet.type=='permutationset')",
                                    cascade='all, delete, delete-orphan')

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        self.external_id = unicode(uuid1())
        
    def is_owned_by(self, user):
        if user:
            return self.owned_by == user.id
        else:
            return False


class QSheet(Base):
    
    __tablename__ = 'qsheets'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Experiment.id, name='qsheets_surveys_fk'))
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    styles = Column(UnicodeText)
    scripts = Column(UnicodeText)
    dataset_id = Column(ForeignKey('data_sets.id', name='qsheets_dataset_id_fk'))

    questions = relationship('Question',
                             backref='qsheet',
                             order_by='Question.order',
                             cascade='all, delete, delete-orphan')
    attributes = relationship('QSheetAttribute',
                              backref='qsheet',
                              cascade='all, delete, delete-orphan')
    next = relationship('QSheetTransition',
                        backref=backref('source', uselist=False),
                        primaryjoin='QSheet.id==QSheetTransition.source_id',
                        order_by='QSheetTransition.order',
                        cascade='all, delete, delete-orphan')
    prev = relationship('QSheetTransition',
                        backref=backref('target', uselist=False),
                        primaryjoin='QSheet.id==QSheetTransition.target_id',
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
    
    def valid_buttons(self):
        """Returns a list of valid UI buttons for this :class':`~pyquest.models.QSheet`.
        
        The following values are possible:
        * *finish* - if the :py:class:`~pyquest.models.QSheet` is the last in the
          :py:class:`~pyquest.models.Experiment`;
        * *next* - if there is another :py:class:`~pyquest.models.QSheet` after this one;
        * *more* - if this :py:class:`~pyquest.models.QSheet` has its ``repeat`` attribute
          set to 'repeat';
        * *clear* - if this :py:class:`~pyquest.models.QSheet` has questions that can be
          answered by the user.
    
        :return: A `list` with the valid buttons
        """
        buttons = []
        if self.next:
            for transition in self.next:
                if transition.target:
                    buttons.append('next')
                    break
        if not buttons:
            buttons.append('finish')
        if self.attr_value('repeat') == 'repeat':
            buttons.append('more')
        if (len([q for q in self.questions if q.q_type.answer_schema()])):
            buttons.append('clear');
        return buttons


class QSheetAttribute(Base):
    
    __tablename__ = 'qsheet_attributes'
    
    id = Column(Integer, primary_key=True)
    qsheet_id = Column(ForeignKey(QSheet.id, name='qsheet_attributes_qsheets_fk'))
    key = Column(Unicode(255))
    value = Column(UnicodeText)


class QuestionTypeGroup(Base):

    __tablename__ = 'question_type_groups'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    order = Column(Integer)
    parent_id = Column(ForeignKey(id, name='question_type_groups_parent_fk'))
    enabled = Column(Boolean, default=True)

    parent = relationship('QuestionTypeGroup',
                          backref=backref('children', order_by='QuestionTypeGroup.order', cascade='all, delete-orphan'),
                          remote_side=[id])


class QuestionType(Base, AttributesMixin):
    
    __tablename__ = 'question_types'
    __parent_attr__ = 'parent'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    dbschema = Column(UnicodeText)
    answer_validation = Column(UnicodeText)
    backend = Column(UnicodeText)
    frontend = Column(UnicodeText)
    group_id = Column(ForeignKey(QuestionTypeGroup.id, name='question_type_groups_fk'))
    parent_id = Column(ForeignKey(id, name='question_types_parent_fk'))
    enabled = Column(Boolean, default=True)
    order = Column(Integer)

    q_type_group = relationship(QuestionTypeGroup,
                                backref=backref('q_types',
                                                order_by='QuestionType.order',
                                                cascade='all, delete-orphan'))
    parent = relationship('QuestionType', backref='children', remote_side=[id])


class Question(Base, AttributesMixin):
    """The :class:`~ess.models.Question` represents a single question in
    a :class:`~ess.models.QSheet`.
    """

    __tablename__ = 'questions'
    __parent_attr__ = 'q_type'
    
    id = Column(Integer, primary_key=True)
    qsheet_id = Column(ForeignKey(QSheet.id, name='questions_qsheets_fk'))
    type_id = Column(ForeignKey(QuestionType.id, name='question_types_fk'))
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    required = Column(Boolean)
    help = Column(Unicode(255))
    order = Column(Integer)
    
    answers = relationship('Answer',
                           backref='question',
                           cascade='all, delete, delete-orphan')
    control_answers = relationship('DataItemControlAnswer',
                                   backref='question',
                                   cascade='all, delete, delete-orphan')
    q_type = relationship('QuestionType', backref='questions')


class QSheetTransition(Base):
    
    __tablename__ = 'qsheet_transitions'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(QSheet.id, name='qsheet_transitions_qsheets_source_fk'))
    target_id = Column(ForeignKey(QSheet.id, name='qsheet_transitions_qsheets_target_fk'))
    order = Column(Integer, default=0)
    _condition = Column(UnicodeText)
    _action = Column(UnicodeText)
    
    def set_condition(self, condition):
        if condition:
            self._condition = json.dumps(condition)
        else:
            self._condition = None
    
    def get_condition(self):
        if self._condition:
            return json.loads(self._condition)
        else:
            return None
    
    condition = property(get_condition, set_condition)

class DataSet(Base):

    __tablename__ = 'data_sets'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    owned_by = Column(ForeignKey(User.id, name="data_sets_owned_by_fk"))
    survey_id = Column(ForeignKey(Experiment.id, name="data_sets_survey_id_fk"))
    type = Column(Unicode(20))

    survey = relationship('Experiment')
    items = relationship('DataItem', backref='data_set', cascade='all, delete, delete-orphan')
    qsheets = relationship('QSheet', backref='data_set')
    owner = relationship('User', backref='data_sets')
    attribute_keys = relationship('DataSetAttributeKey', 
                                  backref='dataset',
                                  order_by='DataSetAttributeKey.order',
                                  cascade='all, delete, delete-orphan')

    __mapper_args__ = {'polymorphic_on': type,
                       'polymorphic_identity': 'dataset'}

    def is_owned_by(self, user):
        if user:
            return self.owned_by == user.id
        else:
            return False

    def copy_data(self, newds):
        # TODO: Needs to be moved into the view
        dbsession = DBSession()
        new_keys_for_old = {}
        for ak in self.attribute_keys:
            new_ak = DataSetAttributeKey(key=ak.key, order=ak.order)
            dbsession.add(new_ak)
            newds.attribute_keys.append(new_ak)
            dbsession.flush()
            new_keys_for_old[ak.id] = new_ak.id
        for item in self.items:
            new_item = DataItem(order=item.order, control=item.control)
            for attribute in item.attributes:
                new_attribute = DataItemAttribute(value=attribute.value, key_id=new_keys_for_old[attribute.key_id])
                new_item.attributes.append(new_attribute)
            newds.items.append(new_item)

    def duplicate(self):
        """ Creates and returns a new DataSet which is a copy of this one. The owned_by and survey_id fields are
        left unfilled.
        """
        dbsession = DBSession()
        newds = DataSet(name=self.name, show_in_list=self.show_in_list)
        self.copy_data(newds)
        return newds

class DataSetRelation(Base):
    
    __tablename__ = 'data_set_relations'
    
    id = Column(Integer, primary_key=True)
    subject_id = Column(ForeignKey(DataSet.id, name='data_set_relations_subject_id_fk'))
    object_id = Column(ForeignKey(DataSet.id, name='data_set_relations_object_id_fk'))
    rel = Column(Unicode(255))
    _data = Column(UnicodeText())
    
    subject = relationship('DataSet',
                           backref='subject_of',
                           primaryjoin='DataSet.id==DataSetRelation.subject_id')
    object = relationship('DataSet',
                           backref='object_of',
                           primaryjoin='DataSet.id==DataSetRelation.object_id')

    def get_data(self):
        return json.loads(self._data)
    
    def set_data(self, data):
        self._data = json.dumps(data)
    
    data = property(get_data, set_data)
    
class DataSetAttributeKey(Base):

    __tablename__ = 'data_set_attribute_keys'
    id = Column(Integer, primary_key=True)
    key = Column(Unicode(255))
    order = Column(Integer)
    dataset_id = Column(ForeignKey(DataSet.id, name="data_set_attribute_keys_dataset_id_fk"))
 
    values = relationship('DataItemAttribute',
                          backref='key',
                          cascade='all, delete, delete-orphan')

class DataItem(Base):
    
    __tablename__ = 'data_items'
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(ForeignKey(DataSet.id, name="data_items_dataset_id_fk"))
    order = Column(Integer)
    control = Column(Boolean, default=False)

    attributes = relationship('DataItemAttribute',
                              backref='data_item', 
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

    def sorted_attributes(self):
        return sorted(self.attributes, key = lambda attribute: attribute.key.order)

class DataItemAttribute(Base):
    
    __tablename__ = 'data_item_attributes'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id, name='data_item_attributes_data_items_fk'))
    value = Column(UnicodeText)
    key_id = Column(ForeignKey(DataSetAttributeKey.id, name='data_item_attributes_data_set_attribute_key_fk'))

class DataItemCount(Base):
    
    __tablename__ = 'data_item_counts'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id, name='data_item_counts_data_items_fk'))
    qsheet_id = Column(ForeignKey(QSheet.id, name='data_item_counts_qsheets_fk'))
    count = Column(Integer)

class DataItemControlAnswer(Base):
    
    __tablename__ = 'data_item_control_answers'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id, name='data_item_control_answers_data_items_fk'))
    question_id = Column(ForeignKey(Question.id, name='data_item_control_answers_questions_fk'))
    answer = Column(Unicode(4096))

class PermutationSet(DataSet):
    """ PermutationSet extends DataSet. A PermutationSet is created when a QSheet has tasks and interfaces to permute.
    The DataItems in a PermutationSet are strings representing the individual permutations. A DataSet containing the parts
    of the actual permutation is created when a Participant actually starts the survey. 
    """

    tasks = relationship('DataSetRelation',
                         primaryjoin="and_(PermutationSet.id==DataSetRelation.subject_id, DataSetRelation.rel=='tasks')",
                         uselist=False)
    interfaces = relationship('DataSetRelation',
                              primaryjoin="and_(PermutationSet.id==DataSetRelation.subject_id, DataSetRelation.rel=='interfaces')",
                              uselist=False)

    __mapper_args__ = {'polymorphic_identity': 'permutationset'}

class Participant(Base):
    
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Experiment.id, name='participants_surveys_fk'))
    state = Column(UnicodeText)
    completed = Column(Boolean, default=False)
    permutation_item_id = Column(ForeignKey(DataItem.id, name='participants_data_set_item_id_perm_fk'))

    answers = relationship('Answer',
                           backref='participant',
                           cascade='all, delete, delete-orphan')
    permutation_item = relationship('DataItem',
                                    backref='participants')
    
    def get_state(self):
        if self.state:
            return json.loads(self.state)
        else:
            return None
    
    def set_state(self, new_state):
        self.state = json.dumps(new_state)

class Answer(Base):
    
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column(ForeignKey(Participant.id, name='answers_participants_fk'))
    question_id = Column(ForeignKey(Question.id, name='answers_questions_fk'))
    data_item_id = Column(ForeignKey(DataItem.id, name='answers_data_items_fk'))
    
    values = relationship('AnswerValue',
                          backref='answer',
                          cascade='all, delete, delete-orphan')
    
class AnswerValue(Base):
    
    __tablename__ = 'answer_values'
    
    id = Column(Integer, primary_key=True)
    answer_id = Column(ForeignKey(Answer.id, name='answer_values_answers_fk'))
    name = Column(Unicode(255))
    value = Column(Unicode(4096))

class Notification(Base):

    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Experiment.id, name='notifications_surveys_fk'))
    ntype = Column(Unicode(32))
    value = Column(Integer)
    recipient = Column(Unicode(255))
    timestamp = Column(Integer, default=0)

    def respond(self, dbsession, time_factor):
        response = {'message': None, 'addresses': self.recipient.split(',')}
        participants = dbsession.query(Participant).filter(Participant.survey_id==self.survey.id).all()
        if self.ntype == 'interval':
            time_now = int(time.time())
            if (self.timestamp == 0) or (time_now - self.timestamp) > (self.value * time_factor):
                response['message'] = 'Experiment "%s" has had %d participants.\n' % (self.survey.title, len(participants))

        if self.ntype == 'pcount':
            if (len(participants) >= self.value) and (self.timestamp == 0):
                response['message'] = 'Experiment "%s" has reached the required count of %d participants.\n' % (self.survey.title, self.value)
                
        return response
