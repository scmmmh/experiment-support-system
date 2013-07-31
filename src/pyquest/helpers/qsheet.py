# -*- coding: utf-8 -*-
'''
Created on 20 Jan 2012

@author: mhall
'''
import itertools
from random import shuffle

from decorator import decorator
from genshi.builder import tag, Markup
from genshi.template import TemplateLoader, TemplateNotFound, loader
from pywebtools import form
from re import search
from StringIO import StringIO

from pyquest.models import DBSession, QuestionType

def substitute(text, item, participant=None):
    if text:
        m = search('\${.+?}', text)
        while(m):
            tag = m.group(0)[2:-1]
            if participant and tag == 'pid_':
                text = text.replace(m.group(0), unicode(participant.id))
            elif tag in item:
                text = text.replace(m.group(0), unicode(item[tag]))
            else:
                text = text.replace(m.group(0), tag)
            m = search('\${.+?}', text)
        return text
    else:
        return None

def shuffle_items(items):
    shuffle(items)
    return items

def load_db_template(filename):
    dbsession = DBSession()
    (component, q_type_name) = filename.split('/')
    q_type = dbsession.query(QuestionType).filter(QuestionType.name==q_type_name).first()
    if not q_type:
        raise TemplateNotFound(filename, 'PyQuestionnaire Question Database')
    if component == 'frontend':
        tmpl = '<html xmlns:py="http://genshi.edgewall.org/" py:strip="True">%s</html>' % (q_type.frontend_doc())
    return (filename, q_type_name, StringIO(tmpl), None)

ldr = TemplateLoader([loader.package('pyquest', 'templates/frontend'), load_db_template], auto_reload=True)

def display(question, item, e, number, csrf_token=None, participant=None):
    global ldr
    if question.q_type:
        tmpl = ldr.load('question.html')
        name = 'items.%s.%s' % (item['did'], question.name)
        if e and hasattr(e, 'error_dict') and e.error_dict and name in e.error_dict:
            error_class = 'error'
            error_text = e.error_dict[name]
        else:
            error_class = None
            error_text = None
        return tmpl.generate(name=name,
                             q=question,
                             i=item,
                             sub=substitute,
                             f=form,
                             e=e,
                             error_class=error_class,
                             error_text=error_text,
                             p=participant,
                             shuffle=shuffle_items,
                             Markup=Markup,
                             number=number)
    else:
        return None

def question():
    def wrapper(f, question, item, e, *args, **kwargs):
        tags = f(question, item, e, *args, **kwargs)
        if not isinstance(tags, list):
            tags = [tags]
        if question.title:
            tags.insert(0, tag.hgroup(tag.h1(substitute(question.title, item))))
        return tag.section(tags, class_='question %s' % (question.type))
    return decorator(wrapper)

def question_as_text(question, no_ids=False):
    text = ['  <pq:type>%s</pq:type>' % (question.q_type.name)]
    for schema in question.q_type.backend_schema():
        if schema['type'] == 'question-name':
            text.append('  <pq:name>%s</pq:name>' % (question.name))
        elif schema['type'] == 'question-title':
            text.append('  <pq:title>%s</pq:title>' % (question.title))
        elif schema['type'] == 'question-required':
            text.append('  <pq:required>%s</pq:required>' % ('true' if question.required else 'false'))
        elif schema['type'] == 'question-help':
            text.append('  <pq:help>%s</pq:help>' % (question.help))
        elif schema['type'] in ['unicode', 'richtext', 'int', 'select']:
            if question.attr_value(schema['attr']):
                text.append('  <pq:attribute name="%s">%s</pq:attribute>' % (schema['attr'], question.attr_value(schema['attr'], default='')))
        elif schema['type'] == 'table':
            text.append('  <pq:attribute_group name="%s">' % (schema['attr']))
            for attr_group in question.attr_group(schema['attr'], default=[], multi=True):
                text.append('    <pq:attribute>')
                for column in schema['columns']:
                    text.append('      <pq:value name="%s">%s</pq:value>' % (column['attr'], attr_group.attr_value(column['attr'], default='')))
                text.append('    </pq:attribute>')
            text.append('  </pq:attribute_group>')
    if no_ids:
        text = '<pq:question>\n%s\n</pq:question>' % ('\n'.join(text))
    else:
        text = '<pq:question id="%i">\n%s\n</pq:question>' % (question.id, '\n'.join(text))
    return text

def as_text(qsheet, as_markup=False, no_ids=False):
    text = '\n'.join([question_as_text(q, no_ids=no_ids) for q in qsheet.questions])
    if as_markup:
        return Markup(text)
    else:
        return text

def transition_as_text(transition):
    text = '<pq:transition from="%s"' % transition.source.name

    if transition.target:
        text = text + (' to="%s"' % transition.target.name)
    if transition.condition:
        text = text + (' question_id="%s"' % transition.condition.question_id)
        text = text + (' expected_answer="%s"' % transition.condition.expected_answer)
        if transition.condition.subquestion_name:
            text = text + (' subquestion_name="%s"' % transition.condition.subquestion_name)

    text = text + '/>'

    return Markup(text)

def render_questions(qsheet, item, p, error=None):
    """ Constructs all the question sections for :py:class:`~pyquest.models.QSheet` qsheet. If the attribute 'show-question-numbers' is set to 'yes' then questions which are answerable are given a number. 

    :param qsheet: The :py:class:`~pyquest.models.QSheet` 
    :param item: A data_item (passed on to display)
    :param p: A participant (passed on to display)
    :param error: An error (passed on to display)
    :return A `list` of sections
    """
    sections = []
    e = error
    question_number = 0
    for question in qsheet.questions:
        if (qsheet.attr_value('show-question-numbers', default='yes') == 'yes' and question.q_type.answer_schema()):
            question_number = question_number + 1
        section = display(question, item, e, question_number, participant=p)
        sections.append(section)

    return tag(sections)

def question_type_list(question_type_groups, depth=1):
    tags = []
    for question_type_group in question_type_groups:
        if question_type_group.enabled:
            tags.append(tag.h3(tag.a(question_type_group.title)))
            if question_type_group.children:
                tags.append(tag.div(question_type_list(question_type_group.children, depth + 1), class_='role-accordion-%i' % (depth)))
            else:
                tags.append(tag.ol([tag.li(question_type.title, data_pyquest_name=question_type.name) for question_type in question_type_group.q_types if question_type.enabled]))
    return tag(tags)

def admin_question_type_list(request, question_type_groups, path='', enabled=True):
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
    tags = []
    for question_type_group in question_type_groups:
        if question_type_group.children:
            delete_tag = None
            if path == '' and not qtg_used(question_type_group):
                delete_tag = tag.a('Delete', href=request.route_url('admin.question_types.delete', qtgid=question_type_group.id), class_='button post-submit')
            tags.append(tag.li(form.hidden_field('order.%i' % (question_type_group.id), ','.join(['qtg_%i' % (qtg.id) for qtg in question_type_group.children]), class_='role-order'),
                               form.checkbox('enabled', 'qtg.%s' % (question_type_group.id), None, checked=question_type_group.enabled, label=question_type_group.title, data_pyquest_enabled='true' if enabled else 'false'),
                               tag.a(tag.span(class_='ui-icon ui-icon-triangle-1-e inline-block bottom', style='vertical-align:middle;'), href='#', class_='role-expand hidden'),
                               tag.a(tag.span(class_='ui-icon ui-icon-triangle-1-s inline-block bottom', style='vertical-align:middle;'), href='#', class_='role-collapse'),
                               delete_tag,
                               tag.ol(admin_question_type_list(request, question_type_group.children, '%s.%s' % (path, question_type_group.name), enabled and question_type_group.enabled)),
                               id='qtg_%i' % (question_type_group.id)))
        else:
            tags.append(tag.li(form.hidden_field('order.%i' % (question_type_group.id), ','.join(['qt_%i' % (qt.id) for qt in question_type_group.q_types]), class_='role-order'),
                               form.checkbox('enabled', 'qtg.%s' % (question_type_group.id), None, checked=question_type_group.enabled, label=question_type_group.title, data_pyquest_enabled='true' if enabled else 'false'),
                               tag.a(tag.span(class_='ui-icon ui-icon-triangle-1-e inline-block bottom'), href='#', class_='role-expand'),
                               tag.a(tag.span(class_='ui-icon ui-icon-triangle-1-s inline-block bottom'), href='#', class_='role-collapse hidden'),
                               tag.ol([tag.li(form.checkbox('enabled', 'qt.%s' % (question_type.id), None, checked=question_type.enabled, label=question_type.title, data_pyquest_enabled='true' if enabled and question_type_group.enabled else 'false'), id='qt_%s' % (question_type.id)) for question_type in question_type_group.q_types], class_='hidden'),
                               id='qtg_%i' % (question_type_group.id)))
    return tag(tags)

def transition_sorter(transition):
    """ Specified as the key argument to sorted() calls. Returns value such that transitions with conditions are ordered by
    their id whereas transitions without have a negative value.

    :param transition: the transition whose order key is to be returned
    :return the order key to use
    """
    if transition.condition:
        return transition.id
    else:
        return -1

def transition_destinations(qsheet):
    """ Returns a list of (id, title) tuples for the other qsheets available as transitions for the given qsheet. The
    list is in the form used by PyWebtools select items.

    :param qsheet: the qsheet 
    :return a list of tuples for use in the transitions section of qsheet editing
    """
    return [('', '--- Finish ---')] + [(qs.id, qs.title) for qs in qsheet.survey.qsheets if qs.id != qsheet.id]

def question_list(qsheet):
    """ Returns a list of (id, name) tuples for the questions available on the given sheet. The list is in the form
    used by PyWebtools select items. The actual items are specific to their use in the transitions section of qsheet
    editing: if the question has subquestions then these are added to the list instead of the question itself and the
    subquestion name is attached to both the value (for later use in qsheet edit view) and the name (for display) 
    parts of the tuple.

    :param qsheet: the qsheet 
    :return a list of tuples for use in the transitions section of qsheet editing
    """
    qlist = []
    for question in qsheet.questions:
        if question.q_type.answer_schema():
            if question.attr_value('subquestion.name', default=None, multi=True):
                subqnames = question.attr_value('subquestion.name', default=[], multi=True)
                for name in subqnames:
                    qlist.append((str(question.id) + '.' + name, question.name + '.' + name))
            else:
                qlist.append((question.id, question.name))

    return qlist

def exclusion_pairs(task_count):
    tasks = [chr(i+65) for i in range(int(task_count))] 
    combinations = itertools.combinations(tasks, 2)
    pairs = [('', 'None')]
    for comb in combinations:
        pairs.append(("".join(comb), "".join(comb)))
    return pairs

