# -*- coding: utf-8 -*-
'''
Created on 20 Jan 2012

@author: mhall
'''
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
