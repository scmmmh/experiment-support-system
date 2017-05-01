"""
###################################
:mod:`ess.models` - Database Models
###################################

This module contains all the database-abstraction classes.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import time

from datetime import datetime
from pyramid.decorator import reify
from pywebtools.pyramid.auth.models import User
from pywebtools.sqlalchemy import Base, MutableDict, JSONUnicodeText
from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey,
                        DateTime, Boolean, func)
from sqlalchemy.orm import (relationship, backref)


DB_VERSION = '93591ffbbc1b'
"""The currently required database version."""


class ParentedAttributesMixin(object):

    def __split_attr_key__(self, key):
        if isinstance(key, tuple):
            if hasattr(self, key[0]):
                return getattr(self, key[0]), key[1]
            elif hasattr(self, 'attributes'):
                return getattr(self, 'attributes'), key[1]
            else:
                return None, None
        elif hasattr(self, 'attributes'):
            return getattr(self, 'attributes'), key
        else:
            return None, None

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


class Preference(Base):

    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(User.id, name='user_preferences_users_fk'), index=True)
    key = Column(Unicode(255))
    value = Column(Unicode(255))

    user = relationship('User', backref='preferences')


class Experiment(Base):

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


class Page(Base, ParentedAttributesMixin):

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
        return len([q for q in self.questions if q['frontend', 'generates_response']]) > 0


class QuestionTypeGroup(Base):

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


class QuestionType(Base, ParentedAttributesMixin):

    __tablename__ = 'question_types'
    __parent_attr__ = 'parent'
    __dict_fields__ = ('id', 'name', 'title', 'backend', 'frontend', 'enabled', 'order')
    __dict_relationships__ = ('q_type_group', 'parent')

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    title = Column(Unicode(255))
    backend = Column(MutableDict.as_mutable(JSONUnicodeText))
    frontend = Column(MutableDict.as_mutable(JSONUnicodeText))
    group_id = Column(ForeignKey(QuestionTypeGroup.id, name='question_type_groups_fk'))
    parent_id = Column(ForeignKey(id, name='question_types_parent_fk'))
    enabled = Column(Boolean, default=True)
    order = Column(Integer)

    q_type_group = relationship(QuestionTypeGroup,
                                backref=backref('q_types',
                                                order_by='QuestionType.order',
                                                cascade='all, delete-orphan'))
    parent = relationship('QuestionType', backref='children', remote_side=[id])


class Question(Base, ParentedAttributesMixin):
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


class Transition(Base, ParentedAttributesMixin):

    __tablename__ = 'transitions'
    __dict_fields__ = ('id', 'order', 'attributes')
    __dict_relationships__ = ('source', 'target')

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(Page.id, name='qsheet_transitions_qsheets_source_fk'))
    target_id = Column(ForeignKey(Page.id, name='qsheet_transitions_qsheets_target_fk'))
    order = Column(Integer, default=0)
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))


class DataSet(Base, ParentedAttributesMixin):

    __tablename__ = 'data_sets'
    __dict_fields__ = ('id', 'name', 'type', 'attributes')
    __dict_relationships__ = ('items', 'experiment', 'pages')

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    experiment_id = Column(ForeignKey(Experiment.id, name="data_sets_experiment_id_fk"))
    type = Column(Unicode(20))
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))

    experiment = relationship('Experiment')
    items = relationship('DataItem',
                         backref='data_set',
                         order_by='DataItem.order',
                         cascade='all, delete, delete-orphan')
    pages = relationship('Page', backref='data_set')


class DataItem(Base, ParentedAttributesMixin):

    __tablename__ = 'data_items'
    __dict_fields__ = ('id', 'order', 'attributes')
    __dict_relationships__ = ('data_set', )

    id = Column(Integer, primary_key=True)
    dataset_id = Column(ForeignKey(DataSet.id, name="data_items_dataset_id_fk"))
    order = Column(Integer)
    control = Column(Boolean)
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))

    answers = relationship('Answer',
                           backref='data_item',
                           cascade='all, delete, delete-orphan')


class Participant(Base, ParentedAttributesMixin):

    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True)
    experiment_id = Column(ForeignKey(Experiment.id, name='participants_experiments_fk'))
    completed = Column(Boolean, default=False)
    started = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))

    answers = relationship('Answer',
                           backref='participant',
                           cascade='all, delete, delete-orphan')


class Answer(Base, ParentedAttributesMixin):

    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True)
    participant_id = Column(ForeignKey(Participant.id, name='answers_participants_fk'))
    question_id = Column(ForeignKey(Question.id, name='answers_questions_fk'))
    data_item_id = Column(ForeignKey(DataItem.id, name='answers_data_items_fk'))
    attributes = Column(MutableDict.as_mutable(JSONUnicodeText))


class Notification(Base):  # TODO: Needs migration / re-build

    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(Experiment.id, name='notifications_experiments_fk'))
    ntype = Column(Unicode(32))
    value = Column(Integer)
    recipient = Column(Unicode(255))
    timestamp = Column(Integer, default=0)

    def respond(self, dbsession, time_factor):
        response = {'message': None, 'addresses': self.recipient.split(',')}
        participants = dbsession.query(Participant).filter(Participant.survey_id == self.survey.id).all()
        if self.ntype == 'interval':
            time_now = int(time.time())
            if (self.timestamp == 0) or (time_now - self.timestamp) > (self.value * time_factor):
                response['message'] = 'Experiment "%s" has had %d participants.\n' % (self.survey.title, len(participants))  # noqa: E501
        if self.ntype == 'pcount':
            if (len(participants) >= self.value) and (self.timestamp == 0):
                response['message'] = 'Experiment "%s" has reached the required count of %d participants.\n' % (self.survey.title, self.value)  # noqa: E501
        return response
