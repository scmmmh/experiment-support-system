# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2012

@author: mhall
'''
import transaction

from formencode import Schema, validators, api, foreach, variabledecode, compound
from lxml import etree
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from sqlalchemy import and_
from pywebtools.auth import is_authorised

from pyquest.views.frontend import safe_int
from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.qsheet import get_q_attr, get_attr_groups, get_qg_attr
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, Survey, QSheet, Question,
    QuestionAttribute, QuestionAttributeGroup, QSheetAttribute)
from pyquest.renderer import render
from pyquest.validation import (PageSchema, flatten_invalid,
                                ValidationState, XmlValidator)

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

class QSheetTextSchema(Schema):
    id = validators.Int()
    text = validators.UnicodeString()
    order = validators.Int()
    
class QSheetBasicQuestionSchema(Schema):
    id = validators.Int(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    help = validators.UnicodeString()
    required = validators.StringBool(if_missing=False)
    order = validators.Int(not_empty=True)

class QSheetNumberQuestionSchema(QSheetBasicQuestionSchema):
    min = validators.Int()
    max = validators.Int()

class QSheetAnswerSchema(Schema):
    value = validators.UnicodeString(not_empty=True)
    label = validators.UnicodeString()
    order = validators.Int(not_empty=True)

class QSheetSubQuestionSchema(Schema):
    name = validators.UnicodeString(not_empty=True)
    label = validators.UnicodeString()
    order = validators.Int(not_empty=True)
    
class QSheetConfirmQuestionSchema(QSheetBasicQuestionSchema):
    value = validators.UnicodeString(not_empty=True)
    label = validators.UnicodeString()

class QSheetVisualSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    name = validators.UnicodeString(not_empty=True)
    title = validators.UnicodeString(not_empty=True)
    styles = validators.UnicodeString()
    scripts = validators.UnicodeString()
    
    pre_validators = [variabledecode.NestedVariables()]
    
class QSheetAddQuestionSchema(Schema):
    type = compound.All(validators.OneOf(['text', 'short_text', 'long_text', 'number',
                                          'email', 'url', 'date', 'time', 'datetime',
                                          'month', 'single_choice', 'single_choice_grid',
                                          'confirm', 'multi_choice',
                                          'multi_choice_grid', 'ranking']),
                        validators.UnicodeString(not_empty=True))

def set_qgroup_attr_value(qgroup, key, value):
    attr = get_qg_attr(qgroup, key)
    if attr:
        attr.value = value
    else:
        qgroup.attributes.append(QuestionAttribute(key=key, value=value))

def set_quest_attr_value(question, key, value):
    attr = get_q_attr(question, key)
    if attr:
        attr.value = value
    else:
        keys = key.split('.')
        for attr_group in question.attributes:
            if attr_group.key == keys[0]:
                attr_group.attributes.append(QuestionAttribute(key=keys[1], value=value))
                return
        qag = QuestionAttributeGroup(key=keys[0])
        qag.attributes.append(QuestionAttribute(key=keys[1], value=value))
        question.attributes.append(qag)
    
@view_config(route_name='survey.qsheet')
@render({'text/html': 'backend/qsheet/index.html'})
def index(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    user = current_user(request)
    if survey:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.view-all")', {'user': user, 'survey': survey}):
            return {'survey': survey}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

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
    seen_ids = []
    for idx, item in enumerate(root):
        q_type = None
        if item.tag == '{http://paths.sheffield.ac.uk/pyquest}static_text':
            q_type = 'text'
        else:
            if 'name' not in item.attrib:
                raise api.Invalid('All questions must have a name', None, None, error_dict={'content': 'All questions must have a name'})
            if item.tag == '{http://paths.sheffield.ac.uk/pyquest}short_text':
                q_type = 'short_text'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}long_text':
                q_type = 'long_text'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}number':
                q_type = 'number'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}email':
                q_type = 'email'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}url':
                q_type = 'url'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}date':
                q_type = 'date'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}time':
                q_type = 'time'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}datetime':
                q_type = 'datetime'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}month':
                q_type = 'month'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}single_choice':
                q_type = 'single_choice'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}single_choice_grid':
                q_type = 'single_choice_grid'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}confirm':
                q_type = 'confirm'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}multi_choice':
                q_type = 'multi_choice'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}multi_choice_grid':
                q_type = 'multi_choice_grid'
            elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}ranking':
                q_type = 'ranking'
        question = None
        if not q_type:
            continue
        if q_type and 'id' in item.attrib:
            question = dbsession.query(Question).filter(and_(Question.id==safe_int(item.attrib['id']),
                                                             Question.qsheet_id==qsheet.id,
                                                             Question.type==q_type)).first()
        if question:
            seen_ids.append(question.id)
        else:
            question = Question(type=q_type)
            qsheet.questions.append(question)
            dbsession.add(question)
        if q_type != 'text':
            question.name = item.attrib['name']
            if 'required' in item.attrib and item.attrib['required'].lower() == 'true':
                question.required = True
            else:
                question.required = False
            if 'title' in item.attrib:
                question.title = item.attrib['title']
            else:
                question.title = ''
            if 'help' in item.attrib:
                question.help = item.attrib['help']
            else:
                question.help = ''
        question.order = idx
        if q_type == 'text':
            text = []
            if item.text:
                text.append(item.text)
            for child in item:
                text.append(etree.tostring(child, encoding="UTF-8"))
            set_quest_attr_value(question, 'text.text', u''.join(text).replace(' xmlns:pq="http://paths.sheffield.ac.uk/pyquest"', ''))
        elif q_type == 'number':
            if 'min' in item.attrib:
                set_quest_attr_value(question, 'further.min', safe_int(item.attrib['min']))
            else:
                set_quest_attr_value(question, 'further.min', None)
            if 'max' in item.attrib:
                set_quest_attr_value(question, 'further.max', safe_int(item.attrib['max']))
            else:
                set_quest_attr_value(question, 'further.max', None)
        elif q_type == 'confirm':
            if 'value' in item.attrib:
                set_quest_attr_value(question, 'further.value', item.attrib['value'])
            else:
                set_quest_attr_value(question, 'further.value', None)
            if 'label' in item.attrib:
                set_quest_attr_value(question, 'further.label', item.attrib['label'])
            else:
                set_quest_attr_value(question, 'further.label', None)
        elif q_type in ['single_choice', 'multi_choice']:
            if 'display' in item.attrib:
                if item.attrib['display'] not in ['table', 'list', 'select']:
                    raise api.Invalid('A choice can only be displayed as table, list, or select.', None, None, error_dict={'content': 'A single choice can only be displayed as table, list, or select.'})
                set_quest_attr_value(question, 'further.subtype', item.attrib['display'])
            else:
                set_quest_attr_value(question, 'further.subtype', 'table')
            if 'allow_other' in item.attrib:
                if item.attrib['allow_other'] not in ['no', 'single']:
                    raise api.Invalid('The allow_other attribute must be either "no" or "single"', None, None, error_dict={'content': 'The allow_other attribute must be either "no" or "single"'})
                set_quest_attr_value(question, 'further.allow_other', item.attrib['allow_other'])
            else:
                set_quest_attr_value(question, 'further.allow_other', 'no')
        if q_type in ['single_choice', 'multi_choice', 'single_choice_grid', 'multi_choice_grid', 'ranking']:
            if 'before_label' in item.attrib:
                set_quest_attr_value(question, 'further.before_label', item.attrib['before_label'])
            if 'after_label' in item.attrib:
                set_quest_attr_value(question, 'further.after_label', item.attrib['after_label'])
            for attr_group in get_attr_groups(question, 'answer'):
                dbsession.delete(attr_group)
            for idx, attr in enumerate(item):
                if attr.tag == '{http://paths.sheffield.ac.uk/pyquest}answer':
                    if 'value' in attr.attrib and 'label' in attr.attrib:
                        if attr.attrib['value'].strip() == '':
                            raise api.Invalid('Every answer must have a value', None, None, error_dict={'content': 'Every answer must have a value'})
                        qag = QuestionAttributeGroup(key='answer', order=idx)
                        qag.attributes.append(QuestionAttribute(key='value', value=attr.attrib['value']))
                        qag.attributes.append(QuestionAttribute(key='label', value=attr.attrib['label']))
                        question.attributes.append(qag)
        if q_type in ['single_choice_grid', 'multi_choice_grid']:
            for attr_group in get_attr_groups(question, 'subquestion'):
                dbsession.delete(attr_group)
            for idx, attr in enumerate(item):
                if attr.tag == '{http://paths.sheffield.ac.uk/pyquest}sub_question':
                    if 'name' in attr.attrib and 'label' in attr.attrib:
                        if attr.attrib['name'].strip() == '':
                            raise api.Invalid('Every question must have a name', None, None, error_dict={'content': 'Every question must have a name'})
                        qag = QuestionAttributeGroup(key='subquestion', order=idx)
                        qag.attributes.append(QuestionAttribute(key='name', value=attr.attrib['name']))
                        qag.attributes.append(QuestionAttribute(key='label', value=attr.attrib['label']))
                        question.attributes.append(qag)
    if cleanup:
        for question in qsheet.questions:
            if question.id and question.id not in seen_ids:
                dbsession.delete(question)
    
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
                            qsheet = QSheet(survey=survey, name=doc.attrib['name'])
                            dbsession.add(qsheet)
                            if 'title' in doc.attrib:
                                qsheet.title = doc.attrib['title']
                            for item in doc:
                                if item.tag == '{http://paths.sheffield.ac.uk/pyquest}styles':
                                    qsheet.styles = item.text
                                elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}scripts':
                                    qsheet.scripts = item.text
                                elif item.tag == '{http://paths.sheffield.ac.uk/pyquest}questions':
                                    load_questions_from_xml(qsheet, item, dbsession, cleanup=False)
                            dbsession.flush()
                            qsid = qsheet.id
                        request.session.flash('Survey page imported', 'info')
                        raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                          sid=request.matchdict['sid'],
                                                          qsid=qsid))
                    else:
                        raise api.Invalid('Invalid XML file', {}, None, error_dict={'source_file': 'The root element of the source file must be {http://paths.sheffield.ac.uk/pyquest}qsheet'})
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
            example = {'did': 0}
            if survey.data_items:
                example['did'] = survey.data_items[0].id
                for attr in survey.data_items[0].attributes:
                    example[attr.key] = attr.value
            if request.method == 'POST':
                validator = PageSchema(qsheet, [example])
                try:
                    validator.to_python(request.POST, ValidationState(request=request))
                except api.Invalid as ie:
                    ie = flatten_invalid(ie)
                    ie.params = request.POST
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'example': example,
                            'e': ie}
            return {'survey': survey,
                    'qsheet': qsheet,
                    'example': example}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

@view_config(route_name='survey.qsheet.edit')
@render({'text/html': 'backend/qsheet/edit.html'})
def edit(request):
    dbsession = DBSession()
    survey = dbsession.query(Survey).filter(Survey.id==request.matchdict['sid']).first()
    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                 QSheet.survey_id==request.matchdict['sid'])).first()
    user = current_user(request)
    if survey and qsheet:
        if is_authorised(':survey.is-owned-by(:user) or :user.has_permission("survey.edit-all")', {'user': user, 'survey': survey}):
            if request.method == 'POST':
                try:
                    schema = QSheetVisualSchema()
                    for question in qsheet.questions:
                        if question.type == 'text':
                            schema.add_field(unicode(question.id), QSheetTextSchema())
                        elif question.type == 'number':
                            schema.add_field(unicode(question.id), QSheetNumberQuestionSchema())
                        elif question.type == 'confirm':
                            schema.add_field(unicode(question.id), QSheetConfirmQuestionSchema())
                        else:
                            sub_schema = QSheetBasicQuestionSchema()
                            if question.type in ['single_choice', 'multi_choice']:
                                sub_schema.add_field('display', validators.OneOf(['table', 'list', 'select']))
                                sub_schema.add_field('allow_other', validators.OneOf(['no', 'single']))
                            if question.type in ['single_choice', 'multi_choice', 'single_choice_grid', 'multi_choice_grid', 'ranking']:
                                sub_schema.add_field('answer', foreach.ForEach(QSheetAnswerSchema()))
                                sub_schema.add_field('before_label', validators.UnicodeString())
                                sub_schema.add_field('after_label', validators.UnicodeString())
                            if question.type in ['single_choice_grid', 'multi_choice_grid']:
                                sub_schema.add_field('sub_quest', foreach.ForEach(QSheetSubQuestionSchema()))
                            schema.add_field(unicode(question.id), sub_schema)
                    params = schema.to_python(request.POST)
                    with transaction.manager:
                        qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                     QSheet.survey_id==request.matchdict['sid'])).first()
                        qsheet.name = params['name']
                        qsheet.title = params['title']
                        qsheet.styles = params['styles']
                        qsheet.scripts = params['scripts']
                        for question in qsheet.questions:
                            q_params = params[unicode(question.id)]
                            if question.type == 'text':
                                question.order = q_params['order']
                                get_q_attr(question, 'text.text').value = q_params['text']
                            else:
                                question.name = q_params['name']
                                question.title = q_params['title']
                                question.help = q_params['help']
                                question.required = q_params['required']
                                question.order = q_params['order']
                                if question.type == 'number':
                                    get_q_attr(question, 'further.min').value = q_params['min']
                                    get_q_attr(question, 'further.max').value = q_params['max']
                                elif question.type == 'confirm':
                                    get_q_attr(question, 'further.value').value = q_params['value']
                                    get_q_attr(question, 'further.label').value = q_params['label']
                                else:
                                    if question.type in ['single_choice', 'multi_choice']:
                                        set_quest_attr_value(question, 'further.subtype', q_params['display'])
                                        set_quest_attr_value(question, 'further.allow_other', q_params['allow_other'])
                                    if question.type in ['single_choice', 'multi_choice', 'single_choice_grid', 'multi_choice_grid', 'ranking']:
                                        set_quest_attr_value(question, 'further.before_label', q_params['before_label'].strip())
                                        set_quest_attr_value(question, 'further.after_label', q_params['after_label'].strip())
                                        new_answers = q_params['answer']
                                        new_answers.sort(key=lambda a: a['order'])
                                        old_answers = get_attr_groups(question, 'answer')
                                        for idx in range(0, max(len(new_answers), len(old_answers))):
                                            if idx < len(new_answers) and idx < len(old_answers):
                                                get_qg_attr(old_answers[idx], 'value').value = new_answers[idx]['value']
                                                get_qg_attr(old_answers[idx], 'label').value = new_answers[idx]['label']
                                                old_answers[idx].order = new_answers[idx]['order']
                                            elif idx < len(new_answers):
                                                qg = QuestionAttributeGroup(key='answer', order=new_answers[idx]['order'])
                                                qg.attributes.append(QuestionAttribute(key='value', value=new_answers[idx]['value']))
                                                qg.attributes.append(QuestionAttribute(key='label', value=new_answers[idx]['label']))
                                                question.attributes.append(qg)
                                                dbsession.add(qg)
                                            elif idx < len(old_answers):
                                                dbsession.delete(old_answers[idx])
                                    if question.type in ['single_choice_grid', 'multi_choice_grid']:
                                        new_subquestion = q_params['sub_quest']
                                        new_subquestion.sort(key=lambda a: a['order'])
                                        old_subquestion = get_attr_groups(question, 'subquestion')
                                        print '-------------'
                                        print old_subquestion
                                        print '-------------'
                                        for idx in range(0, max(len(new_subquestion), len(old_subquestion))):
                                            if idx < len(new_subquestion) and idx < len(old_subquestion):
                                                set_qgroup_attr_value(old_subquestion[idx], 'name', new_subquestion[idx]['name'])
                                                set_qgroup_attr_value(old_subquestion[idx], 'label', new_subquestion[idx]['label'])
                                                old_subquestion[idx].order = new_subquestion[idx]['order']
                                            elif idx < len(new_subquestion):
                                                qg = QuestionAttributeGroup(key='subquestion', order=new_subquestion[idx]['order'])
                                                qg.attributes.append(QuestionAttribute(key='name', value=new_subquestion[idx]['name']))
                                                qg.attributes.append(QuestionAttribute(key='label', value=new_subquestion[idx]['label']))
                                                question.attributes.append(qg)
                                                dbsession.add(qg)
                                            elif idx < len(old_subquestion):
                                                dbsession.delete(old_subquestion[idx])
                        dbsession.add(qsheet)
                    request.session.flash('Survey page updated', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.edit',
                                                      sid=request.matchdict['sid'],
                                                      qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e = flatten_invalid(e)
                    e.params = request.POST
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'e': e}
            else:
                return {'survey': survey,
                        'qsheet': qsheet}
        else:
            redirect_to_login(request)
    else:
        raise HTTPNotFound()

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
                    question = Question(type=params['type'])
                    if params['type'] == 'text':
                        qag = QuestionAttributeGroup(key='text', order=0)
                        qag.attributes.append(QuestionAttribute(key='text', value='<p>Double-click here to edit the text.</p>', order=0))
                        question.attributes.append(qag)
                    elif params['type'] in['number', 'confirm', 'single_choice']:
                        qag = QuestionAttributeGroup(key='further', order=0)
                        if params['type'] == 'number':
                            qag.attributes.append(QuestionAttribute(key='min'))
                            qag.attributes.append(QuestionAttribute(key='max'))
                        elif params['type'] == 'confirm':
                            qag.attributes.append(QuestionAttribute(key='value'))
                            qag.attributes.append(QuestionAttribute(key='label'))
                        elif params['type'] == 'single_choice':
                            qag.attributes.append(QuestionAttribute(key='subtype', value='table'))
                        question.attributes.append(qag)
                        dbsession.add(qag)
                    if params['type'] in ['single_choice', 'multi_choice', 'single_choice_grid', 'multi_choice_grid', 'ranking']:
                        qag = QuestionAttributeGroup(key='answer', order=0)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='answer', order=1)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='answer', order=2)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='answer', order=3)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='answer', order=4)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        dbsession.add(qag)
                    if params['type'] in ['single_choice_grid', 'multi_choice_grid']:
                        qag = QuestionAttributeGroup(key='subquestion', order=0)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='subquestion', order=1)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='subquestion', order=2)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='subquestion', order=3)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        qag = QuestionAttributeGroup(key='subquestion', order=4)
                        qag.attributes.append(QuestionAttribute(key='value'))
                        qag.attributes.append(QuestionAttribute(key='label'))
                        question.attributes.append(qag)
                        dbsession.add(qag)
                    qsheet.questions.append(question)
                    dbsession.add(question)
                    dbsession.flush()
                    qid = question.id
                question = dbsession.query(Question).filter(Question.id==qid).first()
                return {'question': question,
                        'idx': 0}

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
                validator = QSheetSourceSchema()
                try:
                    params = validator.to_python(request.POST)
                    check_csrf_token(request, params)
                    with transaction.manager:
                        qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                     QSheet.survey_id==request.matchdict['sid'])).first()
                        qsheet.name = params['name']
                        qsheet.title = params['title']
                        qsheet.styles = params['styles']
                        qsheet.scripts = params['scripts']
                        for item in params['content']:
                            if item.tag == '{http://paths.sheffield.ac.uk/pyquest}questions':
                                load_questions_from_xml(qsheet, item, dbsession)
                    request.session.flash('Survey page updated', 'info')
                    raise HTTPFound(request.route_url('survey.qsheet.edit.source',
                                                      sid=request.matchdict['sid'],
                                                      qsid=request.matchdict['qsid']))
                except api.Invalid as e:
                    e.params = request.POST
                    qsheet = dbsession.query(QSheet).filter(and_(QSheet.id==request.matchdict['qsid'],
                                                                 QSheet.survey_id==request.matchdict['sid'])).first()
                    return {'survey': survey,
                            'qsheet': qsheet,
                            'e': e}
            else:
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
                raise HTTPFound(request.route_url('survey.qsheet',
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
