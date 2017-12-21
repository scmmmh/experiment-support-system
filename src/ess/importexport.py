"""

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import formencode

from marshmallow import post_load, fields
from offline_jsonapi.schema import Schema
from offline_jsonapi.fields import Relationship
from pywebtools.sqlalchemy import Base
from sqlalchemy import and_

from ess.models import (Experiment, Page, Question, QuestionType, QuestionTypeGroup, DataSet, DataItem, Transition)


class BaseSchema(Schema):

    def get_attribute(self, obj, attr, default):
        if hasattr(obj, attr):
            return getattr(obj, attr)
        try:
            return obj[attr]
        except Exception:
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

    pages = Relationship(schema='PageIOSchema',
                         many=True)
    start = Relationship(schema='PageIOSchema')
    data_sets = Relationship(schema='DataSetIOSchema',
                             many=True)
    latin_squares = Relationship(schema='DataSetIOSchema',
                                 many=True)

    @post_load
    def make_experiment(self, data):
        return Experiment(title=data['title'],
                          summary=data['summary'],
                          styles=data['styles'],
                          scripts=data['scripts'],
                          status='develop',
                          language=data['language'],
                          public=data['public'])

    class Meta():
        type_ = 'experiments'


class PageIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True, allow_none=False)
    title = fields.Str(allow_none=True, missing='')
    scripts = fields.Str(allow_none=True, missing='')
    styles = fields.Str(allow_none=True, missing='')
    attributes = fields.Dict(allow_none=True, missing=None)

    questions = Relationship(schema='QuestionIOSchema',
                             many=True)
    next = Relationship(schema='TransitionIOSchema',
                        many=True)
    prev = Relationship(schema='TransitionIOSchema',
                        many=True)
    data_set = Relationship(schema='DataSetIOSchema',
                            allow_none=True)

    @post_load
    def make_page(self, data):
        page = Page(name=data['name'],
                    title=data['title'],
                    styles=data['styles'],
                    scripts=data['scripts'],
                    attributes=data['attributes'])
        page._import_id = data['id']
        return page

    class Meta():
        type_ = 'pages'


class QuestionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict()

    q_type = Relationship(schema='QuestionTypeIOSchema')

    @post_load
    def make_question(self, data):
        question = Question(order=data['order'],
                            attributes=data['attributes'])
        question._import_id = data['id']
        return question

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

    parent = Relationship(schema='QuestionTypeIOSchema',
                          allow_none=True)
    q_type_group = Relationship(schema='QuestionTypeGroupIOSchema')

    @post_load()
    def make_instance(self, data):
        return QuestionType(name=data['name'],
                            order=data['order'],
                            enabled=data['enabled'],
                            title=data['title'],
                            backend=data['backend'],
                            frontend=data['frontend'])

    class Meta():
        type_ = 'question_types'


class QuestionTypeGroupIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True)
    title = fields.Str(required=True)
    enabled = fields.Boolean(allow_none=True, missing=True)
    order = fields.Int(allow_none=True, missing=1)

    parent = Relationship(schema='QuestionTypeGroupIOSchema',
                          allow_none=True)

    @post_load()
    def make_instance(self, data):
        return QuestionTypeGroup(title=data['title'],
                                 order=data['order'],
                                 enabled=data['enabled'],
                                 name=data['name'])

    class Meta():
        type_ = 'question_type_groups'


class DataSetIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True)
    type = fields.Str(required=True)
    attributes = fields.Dict(allow_none=True)

    items = Relationship(schema='DataItemIOSchema',
                         many=True)

    @post_load
    def make_data_set(self, data):
        data_set = DataSet(name=data['name'],
                           type=data['type'],
                           attributes=data['attributes'])
        data_set._import_id = data['id']
        return data_set

    class Meta():
        type_ = 'data_sets'


class DataItemIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict(allow_none=True)

    @post_load
    def make_data_item(self, data):
        data_item = DataItem(order=data['order'],
                             attributes=data['attributes'])
        data_item._import_id = data['id']
        return data_item

    class Meta():
        type_ = 'data_items'


class TransitionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict(allow_none=True)

    source = Relationship(schema='PageIOSchema')
    target = Relationship(schema='PageIOSchema',
                          allow_none=True)

    @post_load
    def make_transition(self, data):
        return Transition(order=data['order'],
                          attributes=data['attributes'])

    class Meta():
        type_ = 'transitions'


all_io_schemas = [ExperimentIOSchema, PageIOSchema, QuestionIOSchema, QuestionTypeIOSchema, QuestionTypeGroupIOSchema,
                  DataSetIOSchema, DataItemIOSchema, TransitionIOSchema]


def fix_transition(transition, pages):
    """Fixes any references to a page in the ``transition`` conditions (if set).

    :param transition: The transition to apply the fix to
    :type transition: :class:`~ess.models.Transition`
    :param pages: The experiment pages that have been imported
    :type pages: ``list`` of :class:`~ess.models.Page`
    """
    if 'condition' in transition:
        if transition['condition']['type'] == 'answer':
            for page in pages:
                if page._import_id == transition['condition']['page']:
                    transition['condition']['page'] = page.id
                    for question in page.questions:
                        if question._import_id == transition['condition']['question']:
                            transition['condition']['question'] = question.id
                            break
                    break


def fix_latin_square(latin_square, data_sets):
    for data_set in data_sets:
        if latin_square['source_a'] == data_set._import_id:
            latin_square['source_a'] = data_set.id
        elif latin_square['source_b'] == data_set._import_id:
            latin_square['source_b'] = data_set.id
    combinations = []
    # Todo: Combination update does not work
    for comb_set in latin_square['combinations']:
        new_comb_set = []
        for comb_id in comb_set:
            for data_set in data_sets:
                for data_item in data_set.items:
                    if data_item._import_id == comb_id:
                        new_comb_set.append(data_item.id)
        combinations.append(new_comb_set)
    latin_square['combinations'] = combinations



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
                raise formencode.Invalid('No question group "%s" in this installation' % q_type_group_name,
                                         None, None)
            parent = q_type_group
        q_type = dbsession.query(QuestionType).filter(and_(QuestionType.name == q_type_name,
                                                           QuestionType.q_type_group == q_type_group)).first()
        if q_type:
            question.q_type = q_type
        else:
            raise formencode.Invalid('No question type "%s" in this installation' % q_type_name,
                                     None, None)
