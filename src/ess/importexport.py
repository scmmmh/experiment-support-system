"""

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import formencode
import json
import sys

from marshmallow_jsonapi import Schema, fields
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


class ExperimentIOSchema(BaseSchema):

    id = fields.Int()
    title = fields.Str()
    summary = fields.Str()
    styles = fields.Str()
    scripts = fields.Str()
    status = fields.Str()
    language = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    public = fields.Boolean()

    pages = fields.Relationship(many=True,
                                include_resource_linkage=True,
                                type_='pages',
                                schema='PageIOSchema')
    start = fields.Relationship(include_resource_linkage=True,
                                type_='pages',
                                schema='PageIOSchema')

    class Meta():
        type_ = 'experiments'


class PageIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str()
    title = fields.Str()
    scripts = fields.Str()
    styles = fields.Str()
    attributes = fields.Dict()

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

    class Meta():
        type_ = 'pages'


class QuestionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int()
    attributes = fields.Dict()

    q_type = fields.Relationship(include_resource_linkage=True,
                                 type_='question_types',
                                 schema='QuestionTypeIOSchema')

    class Meta():
        type_ = 'questions'


class QuestionTypeIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str()
    title = fields.Str()
    backend = fields.Dict()
    frontend = fields.Dict()
    enabled = fields.Boolean()
    order = fields.Int()

    parent = fields.Relationship(include_resource_linkage=True,
                                 type_='question_types',
                                 schema='QuestionTypeIOSchema',
                                 allow_none=True)
    q_type_group = fields.Relationship(include_resource_linkage=True,
                                       type_='question_type_groups',
                                       schema='QuestionTypeGroupIOSchema')

    class Meta():
        type_ = 'question_types'


class QuestionTypeGroupIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str()
    title = fields.Str()
    enabled = fields.Boolean()
    order = fields.Int()

    parent = fields.Relationship(include_resource_linkage=True,
                                 type_='question_type_groups',
                                 schema='QuestionTypeGroupIOSchema',
                                 allow_none=True)

    class Meta():
        type_ = 'question_type_groups'


class DataSetIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str()
    type = fields.Str()
    attributes = fields.Dict()

    items = fields.Relationship(many=True,
                                include_resource_linkage=True,
                                type_='data_items',
                                schema='DataItemIOSchema')

    class Meta():
        type_ = 'data_sets'


class DataItemIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int()
    attributes = fields.Dict()

    class Meta():
        type_ = 'data_items'


class TransitionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int()
    attributes = fields.Dict()

    class Meta():
        type_ = 'transitions'


def instantiate_page(source, objects, dbsession, state):
    page = dbsession.query(Page).filter(and_(Page.name == source['name'],
                                             Page.experiment_id == state.experiment_id)).first()
    if page:
        raise formencode.Invalid('The experiment already contains a page with this name', source['name'], None)
    page = Page.from_dict(source)
    if 'questions' in source and 'questions' in objects:
        for qid in source['questions']:
            qid = int(qid)
            if qid in objects['questions']:
                question = instantiate_question(objects['questions'][qid], objects, dbsession, state)
                if question:
                    question.page = page
    return page


def instantiate_question(source, objects, dbsession, state):
    question = Question.from_dict(source)
    if 'q_type' in source and 'question_types' in objects:
        qtid = int(source['q_type'])
        if qtid in objects['question_types']:
            question.q_type = instantiate_question_type(objects['question_types'][qtid], objects, dbsession, state)
        else:
            raise formencode.Invalid('Question type missing.')
    else:
        raise formencode.Invalid('Question type missing.')
    return question


def instantiate_question_type(source, objects, dbsession, state):
    if 'q_type_group' in source and 'question_type_groups' in objects:
        qtgid = int(source['q_type_group'])
        if qtgid in objects['question_type_groups']:
            question_type_group = instantiate_question_type_group(objects['question_type_groups'][qtgid], objects, dbsession, state)
            if question_type_group:
                question_type = dbsession.query(QuestionType).filter(and_(QuestionType.name == source['name'],
                                                                          QuestionType.q_type_group == question_type_group)).first()
                if question_type:
                    return question_type
                else:
                    question_type = QuestionType.from_dict(source)
                    question_type.q_type_group = question_type_group
    else:
        raise formencode.Invalid('No question type group specified for the question type')


def instantiate_question_type_group(source, objects, dbsession, state):
    if 'parent' in source:
        if 'question_type_groups' in objects:
            qtgid = int(source['parent'])
            if qtgid in objects['question_type_groups']:
                parent = instantiate_question_type_group(objects['question_type_groups'][qtgid], objects, dbsession, state)
            else:
                raise formencode.Invalid('Parent question type group not found')
        else:
            raise formencode.Invalid('Parent question type group not found')
        question_type_group = dbsession.query(QuestionTypeGroup).filter(and_(QuestionTypeGroup.name == source['name'],
                                                                             QuestionTypeGroup.parent == parent)).first()
    else:
        parent = None
        question_type_group = dbsession.query(QuestionTypeGroup).filter(and_(QuestionTypeGroup.name == source['name'],
                                                                             QuestionTypeGroup.parent == None)).first()
    if not question_type_group:
        question_type_group = QuestionTypeGroup.from_dict(source)
        question_type_group.parent = parent
    return question_type_group


SCHEMA_INST_PAIRS = [(PageIOSchema, instantiate_page), (QuestionIOSchema, instantiate_question),
                     (QuestionTypeIOSchema, instantiate_question_type),
                     (QuestionTypeGroupIOSchema, instantiate_question_type_group), (ExperimentIOSchema, None),
                     (DataSetIOSchema, None)]
SCHEMA_MAPPINGS = dict([(s.Meta.type_, s) for s, _ in SCHEMA_INST_PAIRS])
INSTANTIATION_MAPPINGS = dict([(s.Meta.type_, f) for s, f in SCHEMA_INST_PAIRS])


def import_obj(source):
    schema = SCHEMA_MAPPINGS[source['type']]()
    obj, errors = schema.load({'data': source})
    obj['type_'] = source['type']
    return obj, errors


def instantiate_obj(obj, objects, dbsession, state):
    return INSTANTIATION_MAPPINGS[obj['type_']](obj, objects, dbsession, state)


def import_jsonapi(source, dbsession, state=None):
    source = json.loads(source)
    root = None
    objects = {}
    if 'data' in source:
        root, errors = import_obj(source['data'])
        if errors:
            raise formencode.Invalid('%s: %s' % (source['type'], ' '.join(['%s - %s' % (e['source']['pointer'], e['detail']) for e in errors['errors']])), None, None)
    if 'included' in source:
        for included in source['included']:
            obj, errors = import_obj(included)
            if errors:
                raise formencode.Invalid('%s: %s' % (included['type'], ' '.join(['%s - %s' % (e['source']['pointer'], e['detail']) for e in errors['errors']])), None, None)
            if obj['type_'] not in objects:
                objects[obj['type_']] = {}
            objects[obj['type_']][obj['id']] = obj
    return instantiate_obj(root, objects, dbsession, state)


def export_jsonapi(obj, includes=None, processed=None):
    if processed is None:
        processed = []
    data = getattr(sys.modules[__name__], '%sIOSchema' % obj.__class__.__name__)().dump(obj).data
    if (data['data']['type'], data['data']['id']) in processed:
        return None
    processed.append((data['data']['type'], data['data']['id']))
    included = []
    if includes:
        for class_, method in includes:
            if isinstance(obj, class_):
                attr = getattr(obj, method)
                if isinstance(attr, list):
                    for item in attr:
                        tmp = export_jsonapi(item, includes, processed)
                        if tmp is not None:
                            included.append(tmp['data'])
                            included.extend(tmp['included'])
                elif attr is not None:
                    tmp = export_jsonapi(attr, includes, processed)
                    if tmp is not None:
                        included.append(tmp['data'])
                        included.extend(tmp['included'])
    return {'data': data['data'], 'included': included}
