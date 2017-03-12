"""

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from marshmallow_jsonapi import Schema, fields


class PageIOSchema(Schema):

    id = fields.Int()
    name = fields.Str()
    title = fields.Str()
    scripts = fields.Str()
    styles = fields.Str()
    attributes = fields.Dict()

    questions = fields.Relationship(many=True, include_resource_linkage=True, type_='questions', schema='QuestionIOSchema')

    class Meta():
        type_ = 'pages'

    def __init__(self, *args, **kwargs):
        kwargs['include_data'] = ('questions', )
        Schema.__init__(self, *args, **kwargs)


class QuestionIOSchema(Schema):

    id = fields.Int()
    order = fields.Int()
    attributes = fields.Dict()

    q_type = fields.Relationship(include_resource_linkage=True, type_='question_types', schema='QuestionTypeIOSchema')

    class Meta():
        type_ = 'questions'

    def __init__(self, *args, **kwargs):
        kwargs['include_data'] = ('q_type', )
        Schema.__init__(self, *args, **kwargs)


class QuestionTypeIOSchema(Schema):

    id = fields.Int()
    name = fields.Str()
    title = fields.Str()
    backend = fields.Dict()
    frontend = fields.Dict()
    attributes= fields.Dict()
    enabled = fields.Boolean()
    order = fields.Int()

    parent = fields.Relationship(include_resource_linkage=True, type_='question_types', schema='QuestionTypeIOSchema')
    q_type_group = fields.Relationship(include_resource_linkage=True, type_='question_type_groups', schema='QuestionTypeGroupIOSchema')

    class Meta():
        type_ = 'question_types'

    def __init__(self, *args, **kwargs):
        kwargs['include_data'] = ('parent', 'q_type_group')
        Schema.__init__(self, *args, **kwargs)


class QuestionTypeGroupIOSchema(Schema):

    id = fields.Int()
    name = fields.Str()
    title = fields.Str()
    enabled = fields.Boolean()
    order = fields.Int()

    parent = fields.Relationship(include_resource_linkage=True, type_='question_type_groups', schema='QuestionTypeGroupIOSchema')

    class Meta():
        type_ = 'question_type_groups'

    def __init__(self, *args, **kwargs):
        kwargs['include_data'] = ('parent', )
        Schema.__init__(self, *args, **kwargs)
