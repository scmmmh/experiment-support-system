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
        page = Page(name=data['name'],
                    title=data['title'],
                    styles=data['styles'],
                    scripts=data['scripts'],
                    attributes=data['attributes'],
                    questions=data['questions'] if self.is_sqlalchemy_class(data['questions']) else [],
                    next=data['next'] if self.is_sqlalchemy_class(data['next']) else [],
                    prev=data['prev'] if self.is_sqlalchemy_class(data['prev']) else [],
                    data_set=data['data_set'] if self.is_sqlalchemy_class(data['data_set']) else None)
        page._import_id = data['id']
        return page

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
        question = Question(order=data['order'],
                            attributes=data['attributes'],
                            q_type=data['q_type'] if self.is_sqlalchemy_class(data['q_type']) else None)
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

    parent = fields.Relationship(type_='question_types',
                                 schema='QuestionTypeIOSchema',
                                 allow_none=True)
    q_type_group = fields.Relationship(type_='question_type_groups',
                                       schema='QuestionTypeGroupIOSchema')

    def make_instance(self, data):
        return QuestionType(name=data['name'],
                            order=data['order'],
                            enabled=data['enabled'],
                            title=data['title'],
                            backend=data['backend'],
                            frontend=data['frontend'])
                            #q_type_group=data['q_type_group']
                            #if self.is_sqlalchemy_class(data['q_type_group']) else None,
                            #parent=data['parent']
                            #if 'parent' in data and self.is_sqlalchemy_class(data['parent']) else None)

    class Meta():
        type_ = 'question_types'


class QuestionTypeGroupIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(required=True)
    title = fields.Str(required=True)
    enabled = fields.Boolean(allow_none=True, missing=True)
    order = fields.Int(allow_none=True, missing=1)

    parent = fields.Relationship(type_='question_type_groups',
                                 schema='QuestionTypeGroupIOSchema',
                                 allow_none=True)

    def make_instance(self, data):
        return QuestionTypeGroup(title=data['title'],
                                 order=data['order'],
                                 enabled=data['enabled'],
                                 name=data['name'])
                                 #parent=data['parent']
                                 #if 'parent' in data and self.is_sqlalchemy_class(data['parent']) else None)

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


SCHEMAS = dict([(schema.Meta.type_, schema()) for schema in [QuestionTypeIOSchema,
                                                             QuestionTypeGroupIOSchema]])

def check_valid_jsonapi_obj(data):
    """Check that the ``data`` is a valid JSONAPI object."""
    if 'type' not in data:
        raise Exception('Missing type in object')
    if 'id' not in data:
        raise Exception('Missing id in object')


def load_object(schema, data):
    """Load the object's attributes."""
    check_valid_jsonapi_obj(data)
    if data['type'] != schema.Meta.type_:
        raise Exception('Not the expected data type')
    attributes = data['attributes'] if 'attributes' in data else {}
    values = {}
    for field, validator in schema._declared_fields.items():
        if field != 'id' and not isinstance(validator, fields.Relationship):
            values[field] = validator.deserialize(attributes[field] if field in attributes else None)
    obj = schema.make_instance(values)
    obj._import_source = data
    return obj


def load_relationships(obj, loaded_objs):
    """Load the relationships defined by this object's schema."""
    relationships = obj._import_source['relationships'] if 'relationships' in obj._import_source else {}
    values = {}
    schema = SCHEMAS[obj._import_source['type']]
    for field, validator in schema._declared_fields.items():
        if isinstance(validator, fields.Relationship):
            if not validator.allow_none and field not in relationships:
                raise Exception('Relationship cannot be empty')
            if field in relationships:
                check_valid_jsonapi_obj(relationships[field]['data'])
                if relationships[field]['data']['type'] != validator.type_:
                    raise Exception('Not the expected data type')
                key = (relationships[field]['data']['type'],  relationships[field]['data']['id'])
                if key in loaded_objs:
                    if validator.many:
                        if field in values:
                            values[field].append(loaded_objs[key])
                        else:
                            values[field] = [loaded_objs[key]]
                    else:
                        values[field] = loaded_objs[key]
                else:
                    raise Exception('Reference to missing object %s %s' % key)
    for field, value in values.items():
        setattr(obj, field, value)


def load(schema, data):
    """Load the given ``schema`` from the JSONAPI ``data``"""
    if 'data' not in data:
        raise Exception('Missing data key')  # Todo: Add proper exceptions
    if isinstance(data['data'], list) and schema.many:
        result = []
        loaded_objs = {}
        for data_part in data['data']:
            obj = load_object(schema, data_part)
            loaded_objs[(obj._import_source['type'], obj._import_source['id'])] = obj
            result.append(obj)
    elif isinstance(data['data'], dict) and not schema.many:
        result = load_object(schema, data['data'])
        loaded_objs = {(result._import_source['type'], result._import_source['id']): result}
    else:
        raise Exception('Must be a list with many or a dict without')
    if 'included' in data:
        for included_data in data['included']:
            check_valid_jsonapi_obj(included_data)
            loaded_obj = load_object(SCHEMAS[included_data['type']], included_data)
            loaded_objs[(loaded_obj._import_source['type'], loaded_obj._import_source['id'])] = loaded_obj
    for loaded_obj in loaded_objs.values():
        load_relationships(loaded_obj, loaded_objs)
    return result


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
