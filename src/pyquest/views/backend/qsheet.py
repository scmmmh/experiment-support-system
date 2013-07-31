# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2012

@author: mhall
'''
import transaction
import random
import json

from formencode import Schema, validators, api, variabledecode, foreach
from lxml import etree
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pywebtools.auth import is_authorised
from pywebtools.renderer import render
from sqlalchemy import and_, desc

from pyquest import helpers
from pyquest import taskperms
from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, Question, QuestionAttribute,
                            QuestionAttributeGroup, QSheetAttribute, QSheetTransition,
                            Participant, QuestionType, QuestionTypeGroup, TransitionCondition, DataSet, DataSetAttributeKey, Permutation, DataItem, DataItemAttribute)
from pyquest.validation import (PageSchema, flatten_invalid, ValidationState,
                                XmlValidator, QuestionTypeSchema)


class QSheetNewSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)

class QSheetSourceSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    content = XmlValidator('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest" name="dummy"><pq:questions>%s</pq:questions></pq:qsheet>', strip_wrapper=False)
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()
    repeat = validators.UnicodeString(not_empty=True)
    show_question_numbers = validators.UnicodeString(not_empty=True)
    data_items = validators.Int(if_missing=0, if_empty=0)
    control_items = validators.Int(if_missing=0, if_empty=0)

class ConditionSchema(Schema):
    question_id = validators.String(if_missing=None)
    expected_answer = validators.String()
    subquestion_name = validators.String(if_missing=None)

class TransitionSchema(Schema):
    id = validators.Int(if_missing=0)
    target_id = validators.Int(if_missing=0)
    condition = ConditionSchema(if_missing={})

class QSheetVisualSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()
    repeat = validators.UnicodeString(not_empty=True)
    show_question_numbers = validators.UnicodeString(not_empty=True)
    data_items = validators.Int(if_missing=0, if_empty=0)
    control_items = validators.Int(if_missing=0, if_empty=0)
    transitions = foreach.ForEach(TransitionSchema())
    task_count = validators.Int(if_missing=0, if_empty=0)
    interface_count = validators.Int(if_missing=0, if_empty=0)
    task_worb = validators.UnicodeString()
    interface_worb = validators.UnicodeString()
    task_disallow = validators.UnicodeString()
    interface_disallow = validators.UnicodeString()
    task_order = validators.UnicodeString()
    interface_order = validators.UnicodeString()

    pre_validators = [variabledecode.NestedVariables()]
    
class QSheetAddQuestionSchema(Schema):
    q_type = validators.UnicodeString(not_empty=True)
    order = validators.Int()

NAMESPACES = {'pq': 'http://paths.sheffield.ac.uk/pyquest'}
    
@view_config(route_name='survey.qsheet')
@render({'text/html': True})
def index(request):
    raise HTTPFound(request.route_url('survey.view', sid=request.matchdict['sid']))

@view_config(route_name='survey.qsheet.new')
@render({'text/html': 'backend/qsheet/new.html'})
def new_qsheet(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                validator = QSheetNewSchema()
                try:
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        qsheet = QSheet(name=params['name'],
                                        title=params['title'],
                                        styles='',
                                        scripts='')
                        qsheet.attributes.append(QSheetAttribute(key='repeat', value='single'))
                        qsheet.attributes.append(QSheetAttribute(key='data-items', value='0'))
                        qsheet.attributes.append(QSheetAttribute(key='control-items', value='0'))
                        qsheet.attributes.append(QSheetAttribute(key='show-question-numbers', value='yes'))
                        survey.qsheets.append(qsheet)
                        if not survey.start:
                            survey.start = qsheet
                        dbsession.add(qsheet)
                        dbsession.flush()
                        qsid = qsheet.id
                    request.session.flash('Survey page added', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                      sid=request.matchdict['sid'],
                                                      qsid=qsid))
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'e': e}
            else:
                return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def load_questions_from_xml(qsheet, root, dbsession, cleanup=True):
    def single_xpath_value(element, path, default=None):
        value = element.xpath(path, namespaces=NAMESPACES)
        if value:
            return value[0]
        else:
            return default
    original_ids = [q.id for q in qsheet.questions]
    seen_ids = []
    for idx, item in enumerate(root):
        question = None
        if 'id' in item.attrib:
            question = dbsession.query(Question).filter(and_(Question.id==item.attrib['id'],
                                                             Question.qsheet_id==qsheet.id)).first()
            if question:
                dbsession.add(question)
                seen_ids.append(question.id)
        if not question:
            question = Question()
            qsheet.questions.append(question)
        q_type = dbsession.query(QuestionType).filter(QuestionType.name==single_xpath_value(item, 'pq:type/text()', default=None)).first()
        if q_type:
            question.q_type = q_type
        else:
            raise api.Invalid('Unknown question type', None, None)
        question.order = idx
        for schema in question.q_type.backend_schema():
            if schema['type'] == 'question-name':
                question.name = single_xpath_value(item, 'pq:name/text()', default='unnamed')
            elif schema['type'] == 'question-title':
                question.title = single_xpath_value(item, 'pq:title/text()', default='Missing title')
            elif schema['type'] == 'question-required':
                question.required = True if single_xpath_value(item, 'pq:required/text()', default='false').lower() == 'true' else False
            elif schema['type'] == 'question-help':
                question.help = single_xpath_value(item, 'pq:help/text()', default='')
            elif schema['type'] in ['unicode', 'richtext', 'int', 'select']:
                value = single_xpath_value(item, "pq:attribute[@name='%s']" % (schema['attr']))
                if value is not None:
                    value = etree.tostring(value)
                    value = value[value.find('>') + 1:value.rfind('<')]
                    question.set_attr_value(schema['attr'], value)
                elif 'default' in schema:
                    question.set_attr_value(schema['attr'], schema['default'])
                else:
                    'a'.stop()
                    question.set_attr_value(schema['attr'], '')
            elif schema['type'] == 'table':
                attr_groups = question.attr_group(schema['attr'], default=[], multi=True)
                doc_groups = item.xpath("pq:attribute_group[@name='%s']/pq:attribute" % (schema['attr']), namespaces=NAMESPACES)
                for idx2 in range(0, max(len(attr_groups), len(doc_groups))):
                    if idx2 < len(attr_groups) and idx2 < len(doc_groups):
                        for column in schema['columns']:
                            attr_groups[idx2].set_attr_value(column['attr'], single_xpath_value(doc_groups[idx2], "pq:value[@name='%s']/text()" %(column['attr']), default=column['default'] if 'default' in column else ''))
                    elif idx2 < len(attr_groups):
                        dbsession.delete(attr_groups[idx2])
                    elif idx2 < len(doc_groups):
                        qag = QuestionAttributeGroup(key=schema['attr'], order=idx2)
                        for idx3, column in enumerate(schema['columns']):
                            qag.attributes.append(QuestionAttribute(key=column['attr'],
                                                                    value=single_xpath_value(doc_groups[idx2], "pq:value[@name='%s']/text()" %(column['attr']), default=column['default'] if 'default' in column else ''),
                                                                    order=idx3))
                        question.attributes.append(qag)
    if cleanup:
        remove_ids = [qid for qid in original_ids if qid not in seen_ids]
        dbsession.query(Question).filter(Question.id.in_(remove_ids)).delete()

def load_qsheet_from_xml(survey, doc, dbsession):
    qsheet = QSheet(survey=survey, name=doc.attrib['name'])
    if 'title' in doc.attrib:
        qsheet.title = doc.attrib['title']
    for item in doc:
        if item.tag == '{http://paths.sheffield.ac.uk/pyquest}styles':
            qsheet.styles = item.text
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}scripts':
            qsheet.scripts = item.text
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}attribute':
            qsheet.set_attr_value(item.attrib['name'], item.text)
        elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}questions':
            load_questions_from_xml(qsheet, item, dbsession, cleanup=False)
    return qsheet

def load_transition_from_xml(qsheets, transition, dbsession):
    to_attr = None
    question_id = None
    expected_answer  = None
    subquestion_name = None
    target = None
    from_attr = transition.attrib['from']
    if transition.attrib.has_key('to'):
        to_attr = transition.attrib['to']
        if to_attr in qsheets:
            target = qsheets[to_attr]

    if from_attr in qsheets:
        new_transition = QSheetTransition(source=qsheets[from_attr], target=target)

    if transition.attrib.has_key('question_id'):
        question_id = transition.attrib['question_id']
    if transition.attrib.has_key('expected_answer'):
        expected_answer = transition.attrib['expected_answer']
        new_transition.condition = TransitionCondition(transition_id=new_transition.id, question_id=question_id, expected_answer=expected_answer, subquestion_name=subquestion_name)

    dbsession.add(new_transition)

@view_config(route_name='survey.qsheet.import')
@render({'text/html': 'backend/qsheet/import.html'})
def import_qsheet(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    if 'source_file' not in request.POST or not hasattr(request.POST['source_file'], 'file'):
                        raise api.Invalid('Invalid XML file', {}, None, error_dict={'source_file': 'Please select a file to upload'})
                    doc = XmlValidator('%s').to_python(''.join(request.POST['source_file'].file))
                    if doc.tag == '{http://paths.sheffield.ac.uk/pyquest}qsheet':
                        with transaction.manager:
                            qsheet = load_qsheet_from_xml(survey, doc, dbsession)
                            dbsession.add(qsheet)
                            dbsession.flush()
                            qsid = qsheet.id
                        request.session.flash('Survey page imported', 'info')
                        raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                          sid=request.matchdict['sid'],
                                                          qsid=qsid))
                    else:
                        raise api.Invalid('Invalid XML file', {}, None, error_dict={'source_file': 'Only individual questions can be imported here.'})
                except api.Invalid as e:
                    e.params = request.POST
                    return {'survey': survey,
                            'e': e}
            else:
                return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.view')
@render({'text/html': 'backend/qsheet/view.html'})
def view(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            return {'survey': survey,
                    'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.preview')
@render({'text/html': 'backend/qsheet/preview.html'})
def preview(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            example = [{'did': 0}]
            if qsheet.data_set:
                example[0]['did'] = qsheet.data_set.items[0].id
                for attr in qsheet.data_set.items[0].attributes:
                    example[0][attr.key.key] = attr.value
            if request.method == 'POST':
                validator = PageSchema(qsheet, example)
                try:
                    validator.to_python(request.POST, ValidationState(request=request))
                except api.Invalid as ie:
                    ie = flatten_invalid(ie)
                    ie.params = request.POST
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'data_items': example,
                            'participant': Participant(id=-1),
                            'control': None,
                            'progress': None,
                            'submit_options': ['test-validate'],
                            'e': ie}
            return {'survey': survey,
                    'qsheet': qsheet,
                    'data_items': example,
                    'participant': Participant(id=-1),
                    'control': None,
                    'progress': None,
                    'submit_options': ['test-validate']}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def perm_string_to_dataset(dbsession, perm, survey):
    # convert the bits of perm into a DataSet
    ds = DataSet(name="perm", show_in_list=False)
    dsak = DataSetAttributeKey(key='perm', order=1)
    dbsession.add(ds)
    ds.attribute_keys.append(dsak)
    li = perm
    o = 1
    for item in li:
        di = DataItem(order=o)
        dbsession.add(di)
        dia = DataItemAttribute(value=str(item))
        di.attributes.append(dia)
        ds.items.append(di)
        dsak.values.append(dia)
        o = o + 1
    return ds

@view_config(route_name='survey.qsheet.edit')
@render({'text/html': 'backend/qsheet/edit.html',
         'application/json': True})
def edit(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            question_type_groups = dbsession.query(QuestionTypeGroup).filter(and_(QuestionTypeGroup.parent_id==None, QuestionTypeGroup.enabled==True)).order_by(QuestionTypeGroup.order)
            if request.method == 'POST':
                try:
                    schema = QSheetVisualSchema()
                    for question in qsheet.questions:
                        sub_schema = QuestionTypeSchema(question.q_type.backend_schema())
                        sub_schema.add_field('id', validators.Int(not_empty=True))
                        sub_schema.add_field('order', validators.Int(not_empty=True))
                        schema.add_field(unicode(question.id), sub_schema)
                    params = schema.to_python(request.POST)
                    with transaction.manager:
                        qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                     QSheet.survey_id==request.matchdict['sid'])).first()
                        qsheet.name = params['name']
                        qsheet.title = params['title']
                        qsheet.styles = params['styles']
                        qsheet.scripts = params['scripts']
                        qsheet.set_attr_value('repeat', params['repeat'])
                        qsheet.set_attr_value('show-question-numbers', params['show_question_numbers'])
                        qsheet.set_attr_value('data-items', params['data_items'])
                        qsheet.set_attr_value('control-items', params['control_items'])
                        qsheet.set_attr_value('task-count', params['task_count'])
                        qsheet.set_attr_value('interface-count', params['interface_count'])
                        qsheet.set_attr_value('task-worb', params['task_worb'])
                        qsheet.set_attr_value('interface-worb', params['interface_worb'])
                        qsheet.set_attr_value('task-disallow', params['task_disallow'])
                        qsheet.set_attr_value('interface-disallow', params['interface_disallow'])
                        qsheet.set_attr_value('task-order', params['task_order'])
                        qsheet.set_attr_value('interface-order', params['interface_order'])
                        dbsession.add(survey)
                        dbsession.add(user)
                        for perm in survey.permutations:
                            dbsession.delete(perm.dataset)
                            dbsession.delete(perm)
                        
                        permutations = taskperms.getPermutations(params['task_worb'] + params['interface_worb'], params['task_count'], params['interface_count'], False, params['task_disallow'], params['interface_disallow'], params['task_order'], params['interface_order'])
                        for perm in permutations:
                            pds = perm_string_to_dataset(dbsession, perm, survey)
                            dbsession.add(pds)
                            user.data_sets.append(pds)
                            survey.data_sets.append(pds)
                            p = Permutation(dataset = pds, applicant=qsheet)
                            dbsession.add(p)
                            survey.permutations.append(p)
                            
                        for transition in qsheet.next:
                            t_param = next(t_param for t_param in params['transitions'] if t_param['id'] == transition.id)
                            transition.target_id = t_param['target_id']
                            if len(t_param['condition']) != 0:
                                 transition.condition.expected_answer = t_param['condition']['expected_answer']
                                 vals = t_param['condition']['question_id'].split('.')
                                 transition.condition.question_id = int(vals[0])
                                 if len(vals) == 2:
                                     transition.condition.subquestion_name = vals[1]

                        for question in qsheet.questions:
                            q_params = params[unicode(question.id)]
                            for field in question.q_type.backend_schema():
                                if field['type'] == 'question-name':
                                    question.name = q_params['name']
                                elif field['type'] == 'question-title':
                                    question.title = q_params['title']
                                elif field['type'] == 'question-help':
                                    question.help = q_params['help']
                                elif field['type'] == 'question-required':
                                    question.required = q_params['required']
                                elif field['type'] in ['richtext', 'unicode', 'int', 'select']:
                                    question.set_attr_value(field['attr'], q_params[field['name']])
                                elif field['type'] == 'table':
                                    q_params[field['name']].sort(key=lambda i: i['_order'])
                                    for value, attr_group in zip(q_params[field['name']], question.attr_group(field['name'], default=[], multi=True)):
                                        for column in field['columns']:
                                            attr_group.set_attr_value(column['attr'], value[column['name']])
                                    for value in q_params[field['name']][len(question.attr_group(field['name'], default=[], multi=True)):]:
                                        attr_group = QuestionAttributeGroup(key=field['name'], order=value['_order'])
                                        for column in field['columns']:
                                            attr_group.set_attr_value(column['attr'], value[column['name']])
                                        dbsession.add(attr_group)
                                        question.attributes.append(attr_group)
                                    for attr_group in question.attr_group(field['name'], multi=True)[len(q_params[field['name']]):]:
                                        dbsession.delete(attr_group)
                        dbsession.add(qsheet)
                    if request.is_xhr:
                        return {'flash': 'Survey page updated'}
                    else:
                        request.session.flash('Survey page updated', 'info')
                        raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                          sid=request.matchdict['sid'],
                                                          qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e = flatten_invalid(e)
                    e.params = request.POST
                    if request.is_xhr:
                        return {'e': e}
                    else:
                        return {'survey': survey,
                                'qsheet': qsheet,
                                'question_type_groups': question_type_groups,
                                'e': e}
            else:
                # This is for backwards compatibility. An old qsheet with a 'Finish' transition will have next=[]
                if len(qsheet.next) == 0:
                    new_transition = QSheetTransition(source_id=qsheet.id)
                    qsheet.next = [new_transition]
                    dbsession.add(new_transition)
                return {'survey': survey,
                        'qsheet': qsheet,
                        'question_type_groups': question_type_groups}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

def add_condition(dbsession, qsheet):
    if len(helpers.qsheet.question_list(qsheet)) > 0:
        new_transition = QSheetTransition(source_id = qsheet.id)
        new_transition.condition = TransitionCondition(transition_id = new_transition.id, expected_answer = '')
        qsheet.next.append(new_transition)
        dbsession.add(new_transition)

@view_config(route_name='survey.qsheet.edit.add_condition')
@render({'text/html': 'backend/qsheet/transitions.html'})
def edit_add_condition(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()

    add_condition(dbsession, qsheet)

    return {'qsheet': qsheet,
            'h' : helpers,
            'source' : False}

def delete_condition(dbsession, qsheet):
    to_delete = dbsession.query(QSheetTransition).filter(and_(QSheetTransition.source_id==qsheet.id, QSheetTransition.condition!=None)).order_by(desc(QSheetTransition.id)).first()
    if to_delete:
        qsheet.next.remove(to_delete)

@view_config(route_name='survey.qsheet.edit.delete_condition')
@render({'text/html': 'backend/qsheet/transitions.html'})
def edit_delete_condition(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()

    delete_condition(dbsession, qsheet)

    return {'qsheet': qsheet,
            'h' : helpers,
            'source' : False}

@view_config(route_name='survey.qsheet.edit.add_question')
@render({'text/html': 'backend/qsheet/edit_fragment.html'}, allow_cache=False)
# TODO: CSRF Protection
def edit_add_question(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                params = QSheetAddQuestionSchema().to_python(request.POST)
                with transaction.manager:
                    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                 QSheet.survey_id==request.matchdict['sid'])).first()
                    q_type = dbsession.query(QuestionType).filter(QuestionType.name==params['q_type']).first()
                    if not q_type:
                        raise HTTPNotFound()
                    for quest in qsheet.questions:
                        if quest.order >= params['order']:
                            quest.order = quest.order + 1
                    question = Question(order=params['order'], q_type=q_type)
                    for entry in q_type.dbschema_schema():
                        if entry['type'] == 'attr':
                            question.set_attr_value(entry['attr'], entry['default'], entry['order'] if 'order' in entry else 0, entry['group_order'] if 'group_order' in entry else 0)
                        elif entry['type'] == 'core':
                            if hasattr(question, entry['attr']):
                                setattr(question, entry['attr'], entry['default'])
                    qsheet.questions.append(question)
                    dbsession.add(question)
                    dbsession.flush()
                    qid = question.id
                question = dbsession.query(Question).filter(Question.id==qid).first()
                return {'question': question,
                        'idx': 0}

@view_config(route_name='survey.qsheet.pcount')
@render({'text/html': 'backend/qsheet/taskperms.html'})
def calculate_pcount(request):
    dbsession = DBSession()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()

    pcount = taskperms.countPermutations(request.params['worb'], request.params['tcount'], request.params['icount'], False, request.params['tcon'], request.params['icon'], request.params['tord'], request.params['iord'])
    qsheet.set_attr_value('task-count', request.params['tcount'])
    qsheet.set_attr_value('interface-count', request.params['icount'])
    qsheet.set_attr_value('task-worb', request.params['worb'][0])
    qsheet.set_attr_value('interface-worb', request.params['worb'][1])
    qsheet.set_attr_value('task-disallow', request.params['tcon'])
    qsheet.set_attr_value('interface-disallow', request.params['icon'])
    qsheet.set_attr_value('task-order', request.params['tord'])
    qsheet.set_attr_value('interface-order', request.params['iord'])
    tlist = [chr(i+65) for i in range(int(request.params['tcount']))]
    ilist = [chr(i+49) for i in range(int(request.params['icount']))]
    return {'h' : helpers,
            'qsheet' : qsheet,
            'pcount': str(pcount),
            'exclusion_pairs': [('', 'None')]}

@view_config(route_name='survey.qsheet.edit.delete_question')
@render({'application/json': ''})
# TODO: CSRF Protection
def edit_delete_question(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                with transaction.manager:
                    question = dbsession.query(Question).filter(and_(Question.id==request.matchdict['qid'],
                                                                     Question.qsheet_id==request.matchdict['qsid'])).first()
                    dbsession.delete(question)
                return {'status': 'ok'}

@view_config(route_name='survey.qsheet.edit.source')
@render({'text/html': 'backend/qsheet/edit_source.html'})
def edit_source(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                if request.POST.has_key('sbutton'):
                    if request.POST['sbutton'] == 'AddCondition':
                        add_condition(dbsession, qsheet)
                    else:
                        delete_condition(dbsession, qsheet)
                validator = QSheetSourceSchema()
                try:
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                        qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                     QSheet.survey_id==request.matchdict['sid'])).first()
                        qsheet.name = params['name']
                        qsheet.title = params['title']
                        qsheet.styles = params['styles']
                        qsheet.scripts = params['scripts']
                        qsheet.set_attr_value('repeat', params['repeat'])
                        qsheet.set_attr_value('show-question-numbers', params['show_question_numbers'])
                        qsheet.set_attr_value('data-items', params['data_items'])
                        qsheet.set_attr_value('control-items', params['control_items'])
                        qsheet.set_attr_value('task-count', params['task_count'])
                        qsheet.set_attr_value('interface-count', params['interface_count'])
                        qsheet.set_attr_value('task-worb', params['task_worb'])
                        qsheet.set_attr_value('interface-worb', params['interface_worb'])
                        qsheet.set_attr_value('task-disallow', params['task_disallow'])
                        qsheet.set_attr_value('interface-disallow', params['interface_disallow'])
                        qsheet.set_attr_value('task-order', params['task_order'])
                        qsheet.set_attr_value('interface-order', params['interface_order'])
                        next_qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==params['transition'],
                                                                          QSheet.survey_id==request.matchdict['sid'])).first()

                        for transition in qsheet.next:
                            t_param = next(t_param for t_param in params['transitions'] if t_param['id'] == transition.id)
                            transition.target_id = t_param['target_id']
                            if len(t_param['condition']) != 0:
                                 transition.condition.expected_answer = t_param['condition']['expected_answer']
                                 vals = t_param['condition']['question_id'].split('.')
                                 transition.condition.question_id = int(vals[0])
                                 if len(vals) == 2:
                                     transition.condition.subquestion_name = vals[1]

                        for item in params['content']:
                            if item.tag == '{http://paths.sheffield.ac.uk/pyquest}questions':
                                load_questions_from_xml(qsheet, item, dbsession)
                    request.session.flash('Survey page updated', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.edit.source',
                                                      sid=request.matchdict['sid'],
                                                      qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e.params = request.POST
                    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                 QSheet.survey_id==request.matchdict['sid'])).first()
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'e': e}
            else:
                # This is for backwards compatibility. An old qsheet with a 'Finish' transition will have next=[]
                if len(qsheet.next) == 0:
                    new_transition = QSheetTransition(source_id=qsheet.id)
                    qsheet.next = [new_transition]
                    dbsession.add(new_transition)
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.delete')
@render({'text/html': 'backend/qsheet/delete.html'})
def delete_qsheet(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.delete-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                check_csrf_token(request, request.POST)
                with transaction.manager:
                    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                 QSheet.survey_id==request.matchdict['sid'])).first()
                    if survey.start_id == qsheet.id:
                        survey.start_id = None
                    dbsession.delete(qsheet)
                with transaction.manager:
                    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
                    if not survey.start_id and survey.qsheets:
                        with transaction.manager:
                            survey.start_id = survey.qsheets[0].id
                            dbsession.add(survey)
                request.session.flash('Survey page deleted', 'info')
                raise HTTPFound(request.route_url('survey.view',
                                                  sid=request.matchdict['sid']))
            else:
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.export')
@view_config(route_name='survey.qsheet.export.ext')
@render({'text/html': 'backend/qsheet/export.html',
         'application/xml': 'backend/qsheet/export.xml'})
def export(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            return {'survey': survey,
                    'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()
