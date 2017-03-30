"""

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import json
import sys

from marshmallow_jsonapi import Schema, fields

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


def import_jsonapi(source, dbsession, state=None):
    PageIOSchema().load(json.loads(source))
    
