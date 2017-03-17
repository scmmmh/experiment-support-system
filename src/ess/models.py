# -*- coding: utf-8 -*-
"""
###################################
:mod:`ess.models` - Database Models
###################################

This module contains all the database-abstraction classes.

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json
import time

from datetime import datetime
from pyramid.decorator import reify
from pywebtools.pyramid.auth.models import User
from pywebtools.sqlalchemy import Base, MutableDict, JSONUnicodeText
from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey,
                        DateTime, Boolean, func)
from sqlalchemy.orm import (relationship, backref)


DB_VERSION = '7f8cc2026730'
"""The currently required database version."""


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

    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))


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


class ParentedAttributesMixin(object):

    def __split_attr_key__(self, key):
        if isinstance(key, tuple):
            if hasattr(self, key[0]):
                return getattr(self, key[0]), key[1]
            else:
                return getattr(self, 'attributes'), key[1]
        else:
            return getattr(self, 'attributes'), key

    def __get_attr_parent__(self):
        if hasattr(self, '__parent_attr__') and hasattr(self, self.__parent_attr__):
            return getattr(self, self.__parent_attr__)
        else:
            return None

    def __contains__(self, key):
        attr, sub_key = self.__split_attr_key__(key)
        if attr and sub_key in attr:
            return True
        else:
            parent = self.__get_attr_parent__()
            if parent:
                return key in parent
            else:
                return False 

    def __getitem__(self, key):
        attr, sub_key = self.__split_attr_key__(key)
        if attr and sub_key in attr:
            return attr[sub_key]
        else:
            parent = self.__get_attr_parent__()
            if parent:
                return parent[key]
            else:
                return None

    def __setitem__(self, key, value):
        attr, sub_key = self.__split_attr_key__(key)
        if attr is None:
            if isinstance(key, tuple):
                if hasattr(self, key[0]):
                    setattr(self, key[0], {})
                else:
                    setattr(self, 'attributes', {})
            else:
                setattr(self, 'attributes', {})
            attr, sub_key = self.__split_attr_key__(key)
        attr[sub_key] = value


class AsDictMixin(object):

    def as_dict(self, seen=[]):
        result = {}
        for field_name in self.__dict_fields__:
            attr = getattr(self, field_name)
            if callable(attr):
                result[field_name] = attr()
            else:
                result[field_name] = attr
        if hasattr(self, '__dict_relationships__'):
            for rel_name in self.__dict_relationships__:
                relationship = getattr(self, rel_name)
                if relationship:
                    if callable(relationship):
                        relationship = relationship()
                    if isinstance(relationship, list):
                        result[rel_name] = [r.as_dict(seen + [(r.__class__, r.id)]) for r in relationship if (r.__class__, r.id) not in seen]
                    elif (relationship.__class__, relationship.id) not in seen:
                        result[rel_name] = relationship.as_dict(seen + [(relationship.__class__, relationship.id)])
                    else:
                        result[rel_name] = None
                else:
                    result[rel_name] = None
        return result

    @classmethod
    def from_dict(cls, source):
        inst = cls()
        for field_name in inst.__dict_fields__:
            if field_name == 'id':
                continue
            if field_name in source:
                setattr(inst, field_name, source[field_name])
        return inst


class Preference(Base):
    
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(User.id, name='user_preferences_users_fk'), index=True)
    key = Column(Unicode(255))
    value = Column(Unicode(255))
    
    user = relationship('User', backref='preferences')


class Experiment(Base, AsDictMixin):

    __tablename__ = 'experiments'
    __dict_fields__ = ('id', 'title', 'summary', 'styles', 'scripts', 'status', 'language', 'external_id',
                       'created_at', 'updated_at', 'public')
    __dict_relationships__ = ('pages', 'start', 'data_sets', 'latin_squares')
    
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(1024))
    summary = Column(Unicode(4096))
    styles = Column(UnicodeText)
    scripts = Column(UnicodeText)
    status = Column(Unicode(64))
    start_id = Column(Integer, ForeignKey('pages.id', use_alter=True, name='fk_start_id'))
    language = Column(Unicode(64))
    external_id = Column(Unicode(64), index=True)
    owned_by = Column(ForeignKey(User.id, name='experiments_users_owner_fk'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime)
    public = Column(Boolean, default=True)

    owner = relationship('User', backref='experiments')
    pages = relationship('Page',
                         backref='experiment',
                         primaryjoin='Experiment.id == Page.experiment_id',
                         order_by='Page.name',
                         cascade='all, delete, delete-orphan')
    participants = relationship('Participant',
                                backref='survey',
                                cascade='all, delete, delete-orphan')
    start = relationship('Page',
                         primaryjoin='Experiment.start_id==Page.id',
                         post_update=True)
    notifications = relationship('Notification',
                          backref='survey',
                          cascade='all, delete, delete-orphan')
    data_sets = relationship('DataSet', 
                             primaryjoin="and_(Experiment.id==DataSet.experiment_id, DataSet.type=='dataset')",
                             cascade='all, delete, delete-orphan')
    latin_squares = relationship('DataSet', 
                                 primaryjoin="and_(Experiment.id==DataSet.experiment_id, DataSet.type=='latinsquare')",
                                 cascade='all, delete, delete-orphan')


    def allow(self, action, user):
        if action == 'view':
            if user.id == self.owned_by or user.has_permission('experiment.view'):
                return True
        elif action == 'edit':
            if user.id == self.owned_by or user.has_permission('experiment.edit'):
                return True
        elif action == 'delete':
            if user.id == self.owned_by or user.has_permission('experiment.delete'):
                return True
        return False


class Page(Base, ParentedAttributesMixin, AsDictMixin):
    
    __tablename__ = 'pages'
    __dict_fields__ = ('id', 'name', 'title', 'styles', 'scripts', 'attributes') 
    __dict_relationships__ = ('questions',)
    
    id = Column(Integer, primary_key=True)
    experiment_id = Column(ForeignKey(Experiment.id, name='pages_experiments_fk'))
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    styles = Column(UnicodeText)
    scripts = Column(UnicodeText)
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))
    dataset_id = Column(ForeignKey('data_sets.id', name='pages_dataset_id_fk'))

    questions = relationship('Question',
                             backref='page',
                             order_by='Question.order',
                             cascade='all, delete, delete-orphan')
    next = relationship('Transition',
                        backref=backref('source', uselist=False),
                        primaryjoin='Page.id==Transition.source_id',
                        order_by='Transition.order',
                        cascade='all, delete, delete-orphan')
    prev = relationship('Transition',
                        backref=backref('target', uselist=False),
                        primaryjoin='Page.id==Transition.target_id',
                        cascade='all, delete, delete-orphan')

    @property
    def title_name(self):
        if self.title:
            return self.title
        else:
            return self.name

    @reify
    def has_answerable_questions(self):
        return len([q for q in self.questions if q['frontend', 'display_as'] != 'text']) > 0


class QuestionTypeGroup(Base, AsDictMixin):

    __tablename__ = 'question_type_groups'
    __dict_fields__ = ('id', 'name', 'title', 'enabled', 'order')

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    order = Column(Integer)
    parent_id = Column(ForeignKey(id, name='question_type_groups_parent_fk'))
    enabled = Column(Boolean, default=True)

    parent = relationship('QuestionTypeGroup',
                          backref=backref('children', order_by='QuestionTypeGroup.order', cascade='all, delete-orphan'),
                          remote_side=[id])


class QuestionType(Base, ParentedAttributesMixin, AsDictMixin):
    
    __tablename__ = 'question_types'
    __parent_attr__ = 'parent'
    __dict_fields__ = ('id', 'name', 'title', 'backend', 'frontend', 'attributes', 'enabled', 'order')
    __dict_relationships__ = ('q_type_group', 'parent')
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    dbschema = Column(UnicodeText)
    answer_validation = Column(UnicodeText)
    backend = Column(MutableDict.as_mutable(JSONUnicodeText))
    frontend = Column(MutableDict.as_mutable(JSONUnicodeText))
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))
    group_id = Column(ForeignKey(QuestionTypeGroup.id, name='question_type_groups_fk'))
    parent_id = Column(ForeignKey(id, name='question_types_parent_fk'))
    enabled = Column(Boolean, default=True)
    order = Column(Integer)

    q_type_group = relationship(QuestionTypeGroup,
                                backref=backref('q_types',
                                                order_by='QuestionType.order',
                                                cascade='all, delete-orphan'))
    parent = relationship('QuestionType', backref='children', remote_side=[id])


class Question(Base, ParentedAttributesMixin, AsDictMixin):
    """The :class:`~ess.models.Question` represents a single question in
    a :class:`~ess.models.Page`.
    """

    __tablename__ = 'questions'
    __parent_attr__ = 'q_type'
    __dict_fields__ = ('id', 'order', 'attributes')
    __dict_relationships__ = ('q_type', )
    
    id = Column(Integer, primary_key=True)
    page_id = Column(ForeignKey(Page.id, name='questions_pages_fk'))
    type_id = Column(ForeignKey(QuestionType.id, name='question_types_fk'))
    order = Column(Integer)
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))
    
    answers = relationship('Answer',
                           backref='question',
                           cascade='all, delete, delete-orphan')
    q_type = relationship('QuestionType', backref='questions')


class Transition(Base, AttributesMixin, AsDictMixin):
    
    __tablename__ = 'transitions'
    __dict_fields__ = ('id', 'order', 'attributes')
    __dict_relationships__ = ('source', 'target')
    
    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(Page.id, name='qsheet_transitions_qsheets_source_fk'))
    target_id = Column(ForeignKey(Page.id, name='qsheet_transitions_qsheets_target_fk'))
    order = Column(Integer, default=0)


class DataSet(Base, AttributesMixin, AsDictMixin):

    __tablename__ = 'data_sets'
    __dict_fields__ = ('id', 'name', 'type', 'attributes')
    __dict_relationships__ = ('items', 'experiment', 'pages')

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    experiment_id = Column(ForeignKey(Experiment.id, name="data_sets_experiment_id_fk"))
    type = Column(Unicode(20))

    experiment = relationship('Experiment')
    items = relationship('DataItem', backref='data_set', order_by='DataItem.order', cascade='all, delete, delete-orphan')
    pages = relationship('Page', backref='data_set')


class DataItem(Base, AttributesMixin, AsDictMixin):
    
    __tablename__ = 'data_items'
    __dict_fields__ = ('id', 'order', 'attributes')
    __dict_relationships__ = ('data_set', )

    id = Column(Integer, primary_key=True)
    dataset_id = Column(ForeignKey(DataSet.id, name="data_items_dataset_id_fk"))
    order = Column(Integer)
    control = Column(Boolean)

    counts = relationship('DataItemCount',
                          backref='counts',
                          cascade='all, delete, delete-orphan')
    answers = relationship('Answer',
                           backref='data_item',
                           cascade='all, delete, delete-orphan')


class DataItemCount(Base):
    
    __tablename__ = 'data_item_counts'
    
    id = Column(Integer, primary_key=True)
    data_item_id = Column(ForeignKey(DataItem.id, name='data_item_counts_data_items_fk'))
    page_id = Column(ForeignKey(Page.id, name='data_item_counts_qsheets_fk'))
    count = Column(Integer)


class Participant(Base, AttributesMixin):
    
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    experiment_id = Column(ForeignKey(Experiment.id, name='participants_experiments_fk'))
    completed = Column(Boolean, default=False)
    started = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    answers = relationship('Answer',
                           backref='participant',
                           cascade='all, delete, delete-orphan')


class Answer(Base, AttributesMixin):
    
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column(ForeignKey(Participant.id, name='answers_participants_fk'))
    question_id = Column(ForeignKey(Question.id, name='answers_questions_fk'))
    data_item_id = Column(ForeignKey(DataItem.id, name='answers_data_items_fk'))


class Notification(Base):

    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Experiment.id, name='notifications_experiments_fk'))
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
