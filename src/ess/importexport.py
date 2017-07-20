"""

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import formencode

from marshmallow import post_load
from marshmallow_jsonapi import Schema, fields
from pywebtools.sqlalchemy import Base
from sqlalchemy import and_

from ess.models import (Experiment, Page, Question, QuestionType, QuestionTypeGroup, DataSet, DataItem, Transition)


class BaseSchema(Schema):

    def get_attribute(self, attr, obj, default):
        if hasattr(obj, attr):
            return getattr(obj, attr)
        try:
            return obj[attr]
        except:
            return default

    def is_sqlalchemy_class(self, obj):
        if obj is None:
            return True
        elif isinstance(obj, list):
            for elem in obj:
                if not isinstance(elem, Base):
                    return False
            return True
        else:
            return isinstance(obj, Base)


class ExperimentIOSchema(BaseSchema):

    id = fields.Int()
    title = fields.Str(required=True)
    summary = fields.Str(allow_none=True)
    styles = fields.Str(allow_none=True)
    scripts = fields.Str(allow_none=True)
    status = fields.Str()
    language = fields.Str(allow_none=True)
    public = fields.Boolean()

    pages = fields.Relationship(many=True,
                                include_resource_linkage=True,
                                type_='pages',
                                schema='PageIOSchema')
    start = fields.Relationship(include_resource_linkage=True,
                                type_='pages',
                                schema='PageIOSchema')
    data_sets = fields.Relationship(many=True,
                                    include_resource_linkage=True,
                                    type_='data_sets',
                                    schema='DataSetIOSchema')
    latin_squares = fields.Relationship(many=True,
                                        include_resource_linkage=True,
                                        type_='data_sets',
                                        schema='DataSetIOSchema')

    @post_load
    def make_experiment(self, data):
        return Experiment(title=data['title'],
                          summary=data['summary'],
                          styles=data['styles'],
                          scripts=data['scripts'],
                          status='develop',
                          language=data['language'],
                          public=data['public'],
                          pages=data['pages'] if self.is_sqlalchemy_class(data['pages']) else [],
                          start=data['start'] if self.is_sqlalchemy_class(data['start']) else None,
                          data_sets=data['data_sets'] if self.is_sqlalchemy_class(data['data_sets']) else [],
                          latin_squares=data['latin_squares']
                          if self.is_sqlalchemy_class(data['latin_squares']) else [])

    class Meta():
        type_ = 'experiments'


class PageIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True, allow_none=False)
    title = fields.Str(allow_none=True)
    scripts = fields.Str(allow_none=True)
    styles = fields.Str(allow_none=True)
    attributes = fields.Dict(allow_none=True)

    questions = fields.Relationship(many=True,
                                    include_resource_linkage=True,
                                    type_='questions',
                                    schema='QuestionIOSchema')
    next = fields.Relationship(many=True,
                               include_resource_linkage=True,
                               type_='transitions',
                               schema='TransitionIOSchema')
    prev = fields.Relationship(many=True,
                               include_resource_linkage=True,
                               type_='transitions',
                               schema='TransitionIOSchema')
    data_set = fields.Relationship(include_resource_linkage=True,
                                   type_='data_sets',
                                   schema='DataSetIOSchema',
                                   allow_none=True)

    @post_load
    def make_page(self, data):
        print(data)
        return Page(name=data['name'],
                    title=data['title'],
                    styles=data['styles'],
                    scripts=data['scripts'],
                    attributes=data['attributes'],
                    questions=data['questions'] if self.is_sqlalchemy_class(data['questions']) else [],
                    next=data['next'] if self.is_sqlalchemy_class(data['next']) else [],
                    prev=data['prev'] if self.is_sqlalchemy_class(data['prev']) else [],
                    data_set=data['data_set'] if self.is_sqlalchemy_class(data['data_set']) else None)

    class Meta():
        type_ = 'pages'


class QuestionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict(allow_none=True)

    q_type = fields.Relationship(include_resource_linkage=True,
                                 type_='question_types',
                                 schema='QuestionTypeIOSchema')

    @post_load
    def make_question(self, data):
        return Question(order=data['order'],
                        attributes=data['attributes'],
                        q_type=data['q_type'] if self.is_sqlalchemy_class(data['q_type']) else None)

    class Meta():
        type_ = 'questions'


class QuestionTypeIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True)
    title = fields.Str(required=True)
    backend = fields.Dict(required=True)
    frontend = fields.Dict()
    enabled = fields.Boolean(required=True)
    order = fields.Int(allow_none=True, missing=1)

    parent = fields.Relationship(include_resource_linkage=True,
                                 type_='question_types',
                                 schema='QuestionTypeIOSchema',
                                 allow_none=True)
    q_type_group = fields.Relationship(include_resource_linkage=True,
                                       type_='question_type_groups',
                                       schema='QuestionTypeGroupIOSchema')

    @post_load
    def make_question_type(self, data):
        return QuestionType(name=data['name'],
                            order=data['order'],
                            enabled=data['enabled'],
                            title=data['title'],
                            backend=data['backend'],
                            frontend=data['frontend'],
                            q_type_group=data['q_type_group']
                            if self.is_sqlalchemy_class(data['q_type_group']) else None,
                            parent=data['parent'] if self.is_sqlalchemy_class(data['parent']) else None)

    class Meta():
        type_ = 'question_types'


class QuestionTypeGroupIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True)
    title = fields.Str(required=True)
    enabled = fields.Boolean(allow_none=True, missing=True)
    order = fields.Int(allow_none=True, missing=1)

    parent = fields.Relationship(include_resource_linkage=True,
                                 type_='question_type_groups',
                                 schema='QuestionTypeGroupIOSchema',
                                 allow_none=True)

    @post_load
    def make_question_type_group(self, data):
        return QuestionTypeGroup(title=data['title'],
                                 order=data['order'],
                                 enabled=data['enabled'],
                                 name=data['name'],
                                 parent=data['parent'] if self.is_sqlalchemy_class(data['parent']) else None)

    class Meta():
        type_ = 'question_type_groups'


class DataSetIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True)
    type = fields.Str(required=True)
    attributes = fields.Dict(allow_none=True)

    items = fields.Relationship(many=True,
                                include_resource_linkage=True,
                                type_='data_items',
                                schema='DataItemIOSchema')

    @post_load
    def make_data_set(self, data):
        return DataSet(name=data['name'],
                       type=data['type'],
                       attributes=data['attributes'],
                       items=data['items'] if self.is_sqlalchemy_class(data['items']) else [])

    class Meta():
        type_ = 'data_sets'


class DataItemIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict(allow_none=True)

    @post_load
    def make_data_item(self, data):
        return DataItem(order=data['order'],
                        attributes=data['attributes'])

    class Meta():
        type_ = 'data_items'


class TransitionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict(allow_none=True)

    source = fields.Relationship(include_resource_linkage=True,
                                 type_='pages',
                                 schema='PageIOSchema')
    target = fields.Relationship(include_resource_linkage=True,
                                 type_='pages',
                                 schema='PageIOSchema',
                                 allow_none=True)

    @post_load
    def make_transition(self, data):
        return Transition(order=data['order'],
                          attributes=data['attributes'],
                          source=data['source'] if self.is_sqlalchemy_class(data['source']) else None,
                          target=data['target'] if self.is_sqlalchemy_class(data['target']) else None)

    class Meta():
        type_ = 'transitions'


def replace_questions(page, dbsession):
    """Replace all questions of the page with questions in the local installation.

    :param page: The page for which to replace the questions
    :type page: :class:`~ess.models.Page`
    :param dbsession: The database session to use for querying for the local questions
    :type dbsession: :class:`~pywebtools.sqlalchemy.DBSession`
    """
    def q_type_hierarchy(question_type):
        if question_type is None:
            return []
        if question_type in dbsession:
            dbsession.expunge(question_type)
        hierarchy = [question_type.name]
        group = question_type.q_type_group
        while group is not None:
            if group in dbsession:
                dbsession.expunge(group)
            hierarchy.append(group.name)
            group = group.parent
        return hierarchy

    for question in page.questions:
        hierarchy = q_type_hierarchy(question.q_type)
        q_type_name = hierarchy[0]
        hierarchy = hierarchy[1:]
        parent = None
        while hierarchy:
            q_type_group_name = hierarchy.pop()
            q_type_group = dbsession.query(QuestionTypeGroup).filter(and_(QuestionTypeGroup.name == q_type_group_name,
                                                                          QuestionTypeGroup.parent == parent)).first()
            if not q_type_group:
                raise formencode.Invalid('No question group "%s" in this installation' % q_type_group_name)
            parent = q_type_group
        q_type = dbsession.query(QuestionType).filter(and_(QuestionType.name == q_type_name,
                                                           QuestionType.q_type_group == q_type_group)).first()
        if q_type:
            question.q_type = q_type
        else:
            raise formencode.Invalid('No question type "%s" in this installation' % q_type_group_name)
