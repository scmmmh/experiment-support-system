"""

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import formencode
import json
import sys

from marshmallow import post_load
from marshmallow_jsonapi import Schema, fields
from sqlalchemy import inspect, and_

from ess.models import (Experiment, Page, Question, QuestionType, QuestionTypeGroup, DataSet, DataItem, Transition)


class BaseSchema(Schema):

    def get_attribute(self, attr, obj, default):
        if hasattr(obj, attr):
            return getattr(obj, attr)
        try:
            return obj[attr]
        except:
            return default

    def fix_relationships(self, obj, objs):
        pass

    def clear_relationships(self, obj):
        pass

    def load_existing(self, dbsession, obj, data):
        return obj


class ExperimentIOSchema(BaseSchema):

    id = fields.Int()
    title = fields.Str()
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
        experiment = Experiment(title=data['title'],
                                summary=data['summary'],
                                styles=data['styles'],
                                scripts=data['scripts'],
                                status='develop',
                                language=data['language'],
                                public=data['public'])
        experiment.__import_relationships = {'pages': data['pages'] if 'pages' in data else None,
                                             'start': data['start'] if 'start' in data else None,
                                             'data_sets': data['data_sets'] if 'data_sets' in data else None,
                                             'latin_squares': data['latin_squares']
                                             if 'latin_squares' in data else None}
        return experiment

    def fix_relationships(self, experiment, data):
        if experiment.__import_relationships['pages']:
            for pid in experiment.__import_relationships['pages']:
                if pid is not None:
                    pid = int(pid)
                    if 'pages' in data and pid in data['pages']:
                        experiment.pages.append(data['pages'][pid])
        if experiment.__import_relationships['start'] is not None:
            pid = int(experiment.__import_relationships['start'])
            if 'pages' in data and pid in data['pages']:
                experiment.start = data['pages'][pid]
        if experiment.__import_relationships['data_sets']:
            for dsid in experiment.__import_relationships['data_sets']:
                if dsid is not None:
                    dsid = int(dsid)
                    if 'data_sets' in data and dsid in data['data_sets']:
                        experiment.data_sets.append(data['data_sets'][dsid])
        if experiment.__import_relationships['latin_squares']:
            for dsid in experiment.__import_relationships['latin_squares']:
                if dsid is not None:
                    dsid = int(dsid)
                    if 'data_sets' in data and dsid in data['data_sets']:
                        experiment.latin_squares.append(data['data_sets'][dsid])

    def clear_relationships(self, experiment):
        experiment.pages = []
        experiment.start = None
        experiment.data_sets = []
        experiment.latin_squares = []

    class Meta():
        type_ = 'experiments'


class PageIOSchema(BaseSchema):

    id = fields.Int()
    name = fields.Str(allow_none=False)
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
                    attributes=data['attributes'])
        page.__import_relationships = {'questions': data['questions'] if 'questions' in data else None,
                                       'next': data['next'] if 'next' in data else None,
                                       'prev': data['prev'] if 'prev' in data else None,
                                       'data_set': data['data_set'] if 'data_set' in data else None}
        return page

    def fix_relationships(self, page, data):
        if page.__import_relationships['questions']:
            for qid in page.__import_relationships['questions']:
                if qid is not None:
                    qid = int(qid)
                    if 'questions' in data and qid in data['questions']:
                        page.questions.append(data['questions'][qid])
        if page.__import_relationships['next']:
            for tid in page.__import_relationships['next']:
                if tid is not None:
                    tid = int(tid)
                    if 'transitions' in data and tid in data['transitions']:
                        page.next.append(data['transitions'][tid])
        if page.__import_relationships['prev']:
            for tid in page.__import_relationships['prev']:
                if tid is not None:
                    tid = int(tid)
                    if 'transitions' in data and tid in data['transitions']:
                        page.prev.append(data['transitions'][tid])
        if page.__import_relationships['data_set'] is not None:
            dsid = int(page.__import_relationships['data_set'])
            if 'data_sets' in data and dsid in data['data_sets']:
                page.data_set = data['data_sets'][dsid]

    def clear_relationships(self, page):
        page.questions = []
        page.next = []
        page.prev = []

    class Meta():
        type_ = 'pages'


class QuestionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int()
    attributes = fields.Dict()

    q_type = fields.Relationship(include_resource_linkage=True,
                                 type_='question_types',
                                 schema='QuestionTypeIOSchema')

    @post_load
    def make_question(self, data):
        question = Question(order=data['order'],
                            attributes=data['attributes'])
        question.__import_relationships = {'q_type': data['q_type'] if 'q_type' in data else None}
        return question

    def fix_relationships(self, question, data):
        if question.__import_relationships['q_type'] is not None:
            qtid = int(question.__import_relationships['q_type'])
            if 'question_types' in data and qtid in data['question_types']:
                question.q_type = data['question_types'][qtid]

    def clear_relationships(self, question):
        question.q_type = None

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

    @post_load
    def make_question_type(self, data):
        question_type = QuestionType(name=data['name'],
                                     order=data['order'],
                                     enabled=data['enabled'],
                                     title=data['title'],
                                     backend=data['backend'],
                                     frontend=data['frontend'])
        question_type.__import_relationships = {'parent': data['parent'] if 'parent' in data else None,
                                                'q_type_group': data['q_type_group'] if 'q_type_group' in data
                                                else None}
        return question_type

    def fix_relationships(self, question_type, data):
        if question_type.__import_relationships['parent'] is not None:
            qtid = int(question_type.__import_relationships['parent'])
            if qtid in data['question_types']:
                question_type.parent = data['question_types'][qtid]
        if question_type.__import_relationships['q_type_group'] is not None:
            qtgid = int(question_type.__import_relationships['q_type_group'])
            if qtgid in data['question_type_groups']:
                question_type.q_type_group = data['question_type_groups'][qtgid]

    def clear_relationships(self, question_type):
        question_type.parent = None
        question_type.q_type_group = None

    def load_existing(self, dbsession, obj, data):
        real_obj = None
        if obj['parent'] and obj['q_type_group']:
            state = inspect(obj.parent)
            if state.transient:
                parent = QuestionType().load_existing(dbsession, obj.parent, data)
            else:
                parent = obj.parent
            state = inspect(obj.q_type_group)
            if state.transient:
                q_type_group = QuestionTypeGroup().load_existing(dbsession, obj.q_type_group, data)
            else:
                q_type_group = obj.q_type_group
            real_obj = dbsession.query(QuestionType).filter(and_(QuestionType.name == obj.name,
                                                                 QuestionType.parent == parent,
                                                                 QuestionType.q_type_group == q_type_group)).first()
        elif obj['q_type_group']:
            state = inspect(obj.q_type_group)
            if state.transient:
                q_type_group = QuestionTypeGroup().load_existing(dbsession, obj.q_type_group, data)
            else:
                q_type_group = obj.q_type_group
            real_obj = dbsession.query(QuestionType).filter(and_(QuestionType.name == obj.name,
                                                                 QuestionType.q_type_group == q_type_group)).first()
        else:
            real_obj = dbsession.query(QuestionType).filter(QuestionType.name == obj.name).first()
        if not real_obj:
            raise formencode.Invalid('Cannot be loaded as the question type %s does not exist in this installation.' % obj.name, None, None)  # noqa: E501
        real_obj.__import_relationships = obj.__import_relationships
        return real_obj

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

    @post_load
    def make_question_type_group(self, data):
        question_type_group = QuestionTypeGroup(title=data['title'],
                                                order=data['order'],
                                                enabled=data['enabled'],
                                                name=data['name'])
        question_type_group.__import_relationships = {'parent': data['parent'] if 'parent' in data else None}
        return question_type_group

    def fix_relationships(self, question_type_group, data):
        if question_type_group.__import_relationships['parent'] is not None:
            qtgid = int(question_type_group.__import_relationships['parent'])
            if qtgid in data['question_type_groups']:
                question_type_group.parent = data['question_type_groups'][qtgid]

    def clear_relationships(self, question_type_group):
        question_type_group.parent = None

    def load_existing(self, dbsession, obj, data):
        if obj.parent:
            state = inspect(obj.parent)
            if state.transient:
                parent = QuestionTypeGroupIOSchema().load_existing(dbsession, obj.parent, data)
                real_obj = dbsession.query(QuestionTypeGroup).filter(and_(QuestionTypeGroup.name == obj.name,
                                                                          QuestionTypeGroup.parent == parent)).first()
            else:
                real_obj = dbsession.query(QuestionTypeGroup).\
                    filter(and_(QuestionTypeGroup.name == obj.name,
                                QuestionTypeGroup.parent == obj.parent)).first()
        else:
            real_obj = dbsession.query(QuestionTypeGroup).filter(and_(QuestionTypeGroup.name == obj.name,
                                                                      QuestionTypeGroup.parent == None)).first()
        if not real_obj:
            raise formencode.Invalid('Cannot be loaded as the question group %s does not exist in this installation.' % obj.name, None, None)  # noqa: E501
        real_obj.__import_relationships = obj.__import_relationships
        return real_obj

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

    @post_load
    def make_data_set(self, data):
        data_set = DataSet(name=data['name'],
                           type=data['type'],
                           attributes=data['attributes'])
        data_set.__import_relationships = {'items': data['items'] if 'items' in data else None}
        return data_set

    def fix_relationships(self, data_set, data):
        if data_set.__import_relationships['items'] is not None:
            for diid in data_set.__import_relationships['items']:
                diid = int(diid)
                if diid in data['data_items']:
                    data_set.items.append(data['data_items'][diid])
        if data_set.type == 'latinsquare':
            if 'source_a' in data_set:
                try:
                    dsid = int(data_set['source_a'])
                    if dsid in data['data_sets']:
                        data_set['source_a'] = data['data_sets'][dsid].name
                except:
                    pass
            if 'source_b' in data_set:
                try:
                    dsid = int(data_set['source_b'])
                    if dsid in data['data_sets']:
                        data_set['source_b'] = data['data_sets'][dsid].name
                except:
                    pass

    def clear_relationships(self, question_type_group):
        question_type_group.items = []

    class Meta():
        type_ = 'data_sets'


class DataItemIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict()

    @post_load
    def make_data_item(self, data):
        data_item = DataItem(order=data['order'],
                             attributes=data['attributes'])
        return data_item

    class Meta():
        type_ = 'data_items'


class TransitionIOSchema(BaseSchema):

    id = fields.Int()
    order = fields.Int(allow_none=True, missing=1)
    attributes = fields.Dict()

    source = fields.Relationship(include_resource_linkage=True,
                                 type_='pages',
                                 schema='PageIOSchema')
    target = fields.Relationship(include_resource_linkage=True,
                                 type_='pages',
                                 schema='PageIOSchema')

    @post_load
    def make_transition(self, data):
        transition = Transition(order=data['order'],
                                attributes=data['attributes'])
        transition.__import_relationships = {'source': data['source'] if 'source' in data else None,
                                             'target': data['target'] if 'target' in data else None}
        return transition

    def fix_relationships(self, transition, data):
        if transition.__import_relationships['source'] is not None:
            pid = int(transition.__import_relationships['source'])
            if 'pages' in data and pid in data['pages']:
                transition.source = data['pages'][pid]
        if transition.__import_relationships['target'] is not None:
            pid = int(transition.__import_relationships['target'])
            if 'pages' in data and pid in data['pages']:
                transition.target = data['pages'][pid]

    def clear_relationships(self, transition):
        transition.source = None
        transition.target = None

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


SCHEMA_MAPPINGS = {'experiments': ExperimentIOSchema(),
                   'pages': PageIOSchema(),
                   'questions': QuestionIOSchema(),
                   'question_types': QuestionTypeIOSchema(),
                   'question_type_groups': QuestionTypeGroupIOSchema(),
                   'transitions': TransitionIOSchema(),
                   'data_sets': DataSetIOSchema(),
                   'data_items': DataItemIOSchema()}


def import_jsonapi(source, dbsession, includes=None, existing=None):
    source = json.loads(source)
    objs = {}
    main_obj, errors = SCHEMA_MAPPINGS[source['data']['type']].load(source)
    if errors:
        raise formencode.Invalid(' '.join('%s: %s' % (e['source']['pointer'], e['detail'])
                                          if 'source' in e and 'pointer' in e['source']
                                          else e['detail']
                                          for e in errors['errors'] if 'detail' in e),
                                 None, None)
    objs[source['data']['type']] = {source['data']['id']: main_obj}
    if 'included' in source:
        for include in source['included']:
            obj, sub_errors = SCHEMA_MAPPINGS[include['type']].load({'data': include})
            if include['type'] not in objs:
                objs[include['type']] = {}
            objs[include['type']][include['id']] = obj
            errors.update(sub_errors)
            if errors:
                raise formencode.Invalid('%s: %s' % (include['type'].replace('_', ' ').title(),
                                                     ' '.join('%s: %s' % (e['source']['pointer'], e['detail'])
                                                              if 'source' in e and 'pointer' in e['source']
                                                              else e['detail']
                                                              for e in errors['errors'] if 'detail' in e)),
                                         None, None)
    for type_, items in objs.items():
        for obj in items.values():
            SCHEMA_MAPPINGS[type_].fix_relationships(obj, objs)
    for type_, items in objs.items():
        for id_, obj in list(items.items()):
            if obj.__class__ in existing:
                items[id_] = SCHEMA_MAPPINGS[type_].load_existing(dbsession, obj, objs)
    for type_, items in objs.items():
        for obj in items.values():
            SCHEMA_MAPPINGS[type_].clear_relationships(obj)
    for type_, items in objs.items():
        for obj in items.values():
            SCHEMA_MAPPINGS[type_].fix_relationships(obj, objs)
    return main_obj
