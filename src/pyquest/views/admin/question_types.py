# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import transaction

from formencode import Schema, validators, api, variabledecode, foreach, compound
from lxml import etree
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
#from pywebtools.renderer import render
from sqlalchemy import desc

from pyquest.helpers.auth import check_csrf_token
from pyquest.helpers.user import current_user, redirect_to_login
from pyquest.models import (DBSession, QuestionTypeGroup, QuestionType)
from pyquest.validation import DynamicSchema, XmlValidator, FileReaderValidator

class QuestionTypesSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    enabled = foreach.ForEach(validators.UnicodeString())

    pre_validators = [variabledecode.NestedVariables()]

class QuestionTypesImportSchema(Schema):
    csrf_token = validators.UnicodeString(not_empty=True)
    source_file = compound.Pipe(validators.FieldStorageUploadConverter(not_empty=True), FileReaderValidator(), XmlValidator())

@view_config(route_name='admin.question_types')
#@render({'text/html': 'admin/question_types/index.html'})
def index(request):
    user = current_user(request)
    dbsession = DBSession()
    if user and user.has_permission('admin.question_types'):
        question_type_groups = dbsession.query(QuestionTypeGroup).filter(QuestionTypeGroup.parent_id==None).order_by(QuestionTypeGroup.order)
        if request.method == 'POST':
            try:
                schema = QuestionTypesSchema()
                order = DynamicSchema()
                order.add_field('top', validators.UnicodeString())
                for question_type_group in dbsession.query(QuestionTypeGroup):
                    order.add_field(unicode(question_type_group.id), validators.UnicodeString())
                schema.add_field('order', order)
                params = schema.to_python(request.POST)
                check_csrf_token(request, params)
                orders = {}
                for key, value in params['order'].items():
                    orders[key] = dict([(v, idx) for idx, v in enumerate(value.split(','))])
                with transaction.manager:
                    for question_type_group in dbsession.query(QuestionTypeGroup):
                        question_type_group.enabled = 'qtg.%i' % (question_type_group.id) in params['enabled']
                        if 'qtg_%i' % (question_type_group.id) in orders['top']:
                            question_type_group.order = orders['top']['qtg_%i' % (question_type_group.id)]
                        if '%i' % (question_type_group.id) in orders:
                            if question_type_group.children:
                                for child_qtg in question_type_group.children:
                                    if 'qtg_%i' % (child_qtg.id) in orders[unicode(question_type_group.id)]:
                                        child_qtg.order = orders[unicode(question_type_group.id)]['qtg_%i' % (child_qtg.id)]
                            else:
                                for question_type in question_type_group.q_types:
                                    if 'qt_%i' % (question_type.id) in orders[unicode(question_type_group.id)]:
                                        question_type.order = orders[unicode(question_type_group.id)]['qt_%i' % (question_type.id)]
                    for question_type in dbsession.query(QuestionType):
                        question_type.enabled = 'qt.%i' % (question_type.id) in params['enabled']
            except api.Invalid as e:
                e.params = request.POST
                return {'question_type_groups': question_type_groups,
                        'e': e}
        question_type_groups = dbsession.query(QuestionTypeGroup).filter(QuestionTypeGroup.parent_id==None).order_by(QuestionTypeGroup.order)
        return {'question_type_groups': question_type_groups}
    else:
        redirect_to_login(request)

def load_q_types_from_xml(dbsession, element, order):
    if element.tag == '{https://bitbucket.org/mhall/experiment-support-system}question_type_group':
        question_type_group = QuestionTypeGroup(name=element.attrib['name'], title=element.attrib['title'], order=order)
        for idx, child in enumerate(element):
            child_data = load_q_types_from_xml(dbsession, child, idx)
            if isinstance(child_data, QuestionTypeGroup):
                question_type_group.children.append(child_data)
            elif isinstance(child_data, QuestionType):
                question_type_group.q_types.append(child_data)
        return question_type_group
    elif element.tag == '{https://bitbucket.org/mhall/experiment-support-system}question_type':
        question_type = QuestionType(name=element.attrib['name'], title=element.attrib['title'], order=order)
        for idx, child in enumerate(element):
            if child.tag == '{https://bitbucket.org/mhall/experiment-support-system}dbschema':
                question_type.dbschema = child.text
            elif child.tag == '{https://bitbucket.org/mhall/experiment-support-system}answer_validation':
                question_type.answer_validation = child.text
            elif child.tag == '{https://bitbucket.org/mhall/experiment-support-system}backend':
                question_type.backend = child.text
            elif child.tag == '{https://bitbucket.org/mhall/experiment-support-system}frontend':
                question_type.frontend = child.text
            elif child.tag == '{https://bitbucket.org/mhall/experiment-support-system}inherit_from':
                parent_type = dbsession.query(QuestionType).filter(QuestionType.name==child.text).first()
                question_type.parent = parent_type
        return question_type

@view_config(route_name='admin.question_types.import')
#@render({'text/html': 'admin/question_types/import.html'})
def import_qtypes(request):
    user = current_user(request)
    dbsession = DBSession()
    if user and user.has_permission('admin.question_types'):
        if request.method == 'POST':
            try:
                params = QuestionTypesImportSchema().to_python(request.POST)
                if params['source_file'].tag != '{http://paths.sheffield.ac.uk/pyquest}question_type_group':
                    raise api.Invalid('Invalid XML file', {}, None, error_dict={'source_file': 'The root element must be a {http://paths.sheffield.ac.uk/pyquest}question_type_group.'})
                with transaction.manager:
                    start = dbsession.query(QuestionTypeGroup.order).filter(QuestionTypeGroup.parent_id==None).order_by(desc(QuestionTypeGroup.order)).first()
                    if start:
                        start = start[0] + 1
                    else:
                        start = 0
                    dbsession.add(load_q_types_from_xml(dbsession, params['source_file'], start))
                raise HTTPFound(request.route_url('admin.question_types'))
            except api.Invalid as e:
                e.params = request.POST
                return {'e': e}
        return {}
    else:
        redirect_to_login(request)

@view_config(route_name='admin.question_types.delete')
#@render({'text/html': 'admin/question_types/delete.html'})
def delete_qtypes(request):
    def qtg_used(qtg):
        if qtg.children:
            for child in qtg.children:
                if qtg_used(child):
                    return True
            return False
        else:
            for qt in qtg.q_types:
                if qt.questions or qt.children:
                    return True
            return False
    user = current_user(request)
    dbsession = DBSession()
    if user and user.has_permission('admin.question_types'):
        if request.method == 'POST':
            try:
                with transaction.manager:
                    question_type_group = dbsession.query(QuestionTypeGroup).filter(QuestionTypeGroup.id==request.matchdict['qtgid']).first()
                    if qtg_used(question_type_group):
                        request.session.flash('The question types are in use and can thus not be deleted. Deactivate them instead.', queue='warn')
                        raise HTTPFound(request.route_url('admin.question_types'))
                    dbsession.delete(question_type_group)
                request.session.flash('The question types have been deleted.', queue='info')
                raise HTTPFound(request.route_url('admin.question_types'))
            except api.Invalid as e:
                e.params = request.POST
                return {'e': e}
        return {}
    else:
        redirect_to_login(request)
