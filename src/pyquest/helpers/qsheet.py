# -*- coding: utf-8 -*-
'''
Created on 20 Jan 2012

@author: mhall
'''
from random import shuffle

from decorator import decorator
from genshi.builder import tag, Markup
from pywebtools import form
from re import search

def get_attr_groups(question, key):
    return [attr_group for attr_group in question.attributes if attr_group.key==key]

def get_qs_attr(qsheet, key):
    for attr in qsheet.attributes:
        if attr.key == key:
            return attr
    return None

def get_qs_attr_value(qsheet, key):
    attr = get_qs_attr(qsheet, key)
    if attr:
        return attr.value
    else:
        return None
    
def get_qg_attr(attr_group, key):
    for attr in attr_group.attributes:
        if attr.key == key:
            return attr
    return None

def get_qg_attr_value(attr_group, key):
    attr = get_qg_attr(attr_group, key)
    if attr:
        return attr.value
    else:
        return None
    
def get_q_attr(question, key):
    keys = key.split('.')
    if len(keys) < 2:
        return None
    for attr_group in question.attributes:
        if attr_group.key == keys[0]:
            return get_qg_attr(attr_group, keys[1])
    return None
    
def get_q_attr_value(question, key):
    attr = get_q_attr(question, key)
    if attr:
        return attr.value
    else:
        return None
    
def question_type_title(q_type):
    if q_type == 'text':
        return 'Static text'
    elif q_type == 'short_text':
        return 'Single-line text input'
    elif q_type == 'long_text':
        return 'Multi-line text input'
    elif q_type == 'number':
        return 'Number input'
    elif q_type == 'email':
        return 'E-Mail input'
    elif q_type == 'url':
        return 'URL input'
    elif q_type == 'date':
        return 'Date input'
    elif q_type == 'time':
        return 'Time input'
    elif q_type == 'datetime':
        return 'Date & Time input'
    elif q_type == 'month':
        return 'Month input'
    elif q_type == 'rating':
        return 'Rating'
    elif q_type == 'rating_group':
        return 'Rating grid'
    elif q_type == 'single_list':
        return 'List single choice'
    elif q_type == 'single_select':
        return 'Select single choice'
    elif q_type == 'confirm':
        return 'Confirmation checkbox'
    elif q_type == 'multichoice':
        return 'Multiple choice'
    elif q_type == 'multichoice_group':
        return 'Multiple choice grid'
    elif q_type == 'ranking':
        return 'Ranking'
    else:
        return q_type
    
def substitute(text, item):
    if text:
        m = search('\${.+}', text)
        while(m):
            tag = m.group(0)[2:-1]
            if tag in item:
                text = text.replace(m.group(0), unicode(item[tag]))
            else:
                text = text.replace(m.group(0), tag)
            m = search('\${.+}', text)
        return text
    else:
        return None

def display(question, item, e, csrf_token=None):
    if question.type == 'text':
        return tag.section(Markup(get_q_attr_value(question, 'text.text')))
    elif question.type == 'short_text':
        return short_text_input(question, item, e)
    elif question.type == 'long_text':
        return long_text_input(question, item, e)
    elif question.type == 'number':
        return number_input(question, item, e)
    elif question.type == 'email':
        return email_input(question, item, e)
    elif question.type == 'url':
        return url_input(question, item, e)
    elif question.type == 'date':
        return date_input(question, item, e)
    elif question.type == 'time':
        return time_input(question, item, e)
    elif question.type == 'datetime':
        return datetime_input(question, item, e)
    elif question.type == 'month':
        return month_input(question, item, e)
    elif question.type == 'rating':
        return rating(question, item, e)
    elif question.type == 'rating_group':
        return rating_group(question, item, e)
    elif question.type == 'single_list':
        return single_list(question, item, e)
    elif question.type == 'single_select':
        return single_select(question, item, e)
    elif question.type == 'confirm':
        return confirm(question, item, e)
    elif question.type == 'multichoice':
        return multichoice(question, item, e)
    elif question.type == 'multichoice_group':
        return multichoice_group(question, item, e)
    elif question.type == 'ranking':
        return ranking(question, item, e)
    else:
        return question.type

def question():
    def wrapper(f, question, item, e):
        tags = f(question, item, e)
        if not isinstance(tags, list):
            tags = [tags]
        if question.title:
            tags.insert(0, tag.hgroup(tag.h1(substitute(question.title, item))))
        return tag.section(tags, class_='question %s' % (question.type))
    return decorator(wrapper)

@question()
def short_text_input(question, item, e):
    return tag.p(form.text_field('items.%s.%s' % (item['did'], question.name), '', e))

@question()
def long_text_input(question, item, e):
    return tag.p(form.textarea('items.%s.%s' % (item['did'], question.name), '', e))

@question()    
def number_input(question, item, e):
    attr = {}
    if get_q_attr_value(question, 'further.min').strip() != '':
        attr['min'] = substitute(get_q_attr_value(question, 'further.min'), item)
    if get_q_attr_value(question, 'further.max').strip() != '':
        attr['max'] = substitute(get_q_attr_value(question, 'further.min'), item)
    if get_q_attr_value(question, 'further.step').strip() != '':
        attr['step'] = substitute(get_q_attr_value(question, 'further.min'), item)
    return tag.p(form.number_field('items.%s.%s' % (item['did'], question.name), '', e, **attr))

@question()
def email_input(question, item, e):
    return tag.p(form.email_field('items.%s.%s' % (item['did'], question.name), '', e))
    
@question()
def url_input(question, item, e):
    return tag.p(form.url_field('items.%s.%s' % (item['did'], question.name), '', e))

@question()
def date_input(question, item, e):
    return tag.p(form.date_field('items.%s.%s' % (item['did'], question.name), '' , e))

@question()
def time_input(question, item, e):
    return tag.p(form.time_field('items.%s.%s' % (item['did'], question.name), '' , e))

@question()
def datetime_input(question, item, e):
    return tag.p(form.datetime_field('items.%s.%s' % (item['did'], question.name), '' , e))
        
@question()
def month_input(question, item, e):
    return tag.p(form.month_field('items.%s.%s' % (item['did'], question.name), '' , e))

@question()
def rating(question, item, e):
    rows = []
    answers = get_attr_groups(question, 'answer')
    rows.append(tag.thead(tag.tr(map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers))))
    rows.append(tag.tbody(tag.tr(map(lambda a: tag.td(tag.input(type='radio',
                                                                name='items.%s.%s' % (item['did'], question.name),
                                                                value=get_qg_attr_value(a, 'value'))),
                                     answers))))
    return form.error_wrapper(tag.table(rows), 'items.%s.%s' % (item['did'], question.name), e)

@question()
def rating_group(question, item, e):
    answers = get_attr_groups(question, 'answer')
    rows = []
    field_names = ['items.%s.%s' % (item['did'], question.name)]
    for sub_question in get_attr_groups(question, 'subquestion'):
        rows.append(tag.tr(tag.th(get_qg_attr_value(sub_question, 'label')),
                           map(lambda a: tag.td(tag.input(type='radio',
                                                          name='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')),
                                                          value=get_qg_attr_value(a, 'value'))),
                               answers)))
        field_names.append('items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')))
    return form.error_wrapper(tag.table(tag.thead(tag.tr(tag.th(), map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers))),
                                        tag.tbody(rows)),
                              field_names, e)

@question()
def single_list(question, item, e):
    items = []
    answers = get_attr_groups(question, 'answer')
    for idx, answer in enumerate(answers):
        parts = [tag.input(type='radio',
                           id='items.%s.%s-%i' % (item['did'], question.name, idx),
                           name='items.%s.%s' % (item['did'], question.name),
                           value=get_qg_attr_value(answer, 'value'))]
        if get_qg_attr_value(answer, 'value').strip() != '':
            parts.append(tag.label(get_qg_attr_value(answer, 'value'),
                                   for_='items.%s.%s-%i' % (item['did'], question.name, idx)))
        items.append(tag.li(parts))
    return form.error_wrapper(tag.ul(items), 'items.%s.%s' % (item['did'], question.name), e)

@question()
def single_select(question, item, e):
    answers = get_attr_groups(question, 'answer')
    items = [tag.option(get_qg_attr_value(answer, 'label'), value=get_qg_attr_value(answer, 'value')) for answer in answers]
    items.insert(0, tag.option('--- Please choose ---', value=''))
    return form.error_wrapper(tag.p(tag.select(items,
                                               name='items.%s.%s' % (item['did'], question.name))),
                              'items.%s.%s' % (item['did'], question.name),
                              e)

@question()
def confirm(question, item, e):
    tags = []
    tags.append(tag.input(type='checkbox',
                          id='items.%s.%s' % (item['did'], question.name),
                          name='items.%s.%s' % (item['did'], question.name),
                          value=get_q_attr_value(question, 'further.value')))
    if get_q_attr_value(question, 'further.label').strip() != '':
        tags.append(tag.label(get_q_attr_value(question, 'further.label'),
                              for_='items.%s.%s' % (item['did'], question.name)))
    elif question.title.strip() != '':
        tags.append(tag.label(question.title,
                              for_='items.%s.%s' % (item['did'], question.name)))
    return form.error_wrapper(tag.p(tags), 'items.%s.%s' % (item['did'], question.name), e)
    
@question()
def multichoice(question, item, e):
    rows = []
    answers = get_attr_groups(question, 'answer')
    rows.append(tag.thead(tag.tr(map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers))))
    rows.append(tag.tbody(tag.tr(map(lambda a: tag.td(tag.input(type='checkbox',
                                                                name='items.%s.%s' % (item['did'], question.name),
                                                                value=get_qg_attr_value(a, 'value'))),
                                     answers))))
    return form.error_wrapper(tag.table(rows), 'items.%s.%s' % (item['did'], question.name), e)

@question()
def multichoice_group(question, item, e):
    answers = get_attr_groups(question, 'answer')
    rows = []
    field_names = ['items.%s.%s' % (item['did'], question.name)]
    for sub_question in get_attr_groups(question, 'subquestion'):
        rows.append(tag.tr(tag.th(get_qg_attr_value(sub_question, 'label')),
                           map(lambda a: tag.td(tag.input(type='checkbox',
                                                          name='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')),
                                                          value=get_qg_attr_value(a, 'value'))),
                               answers)))
        field_names.append('items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')))
    return form.error_wrapper(tag.table(tag.thead(tag.tr(tag.th(), map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers))),
                                        tag.tbody(rows)),
                              field_names, e)

@question()
def ranking(question, item, e):
    answers = get_attr_groups(question, 'answer')
    items = []
    for answer in answers:
        items.append(tag.li(tag.select(tag.option('--', value=''),
                                       [tag.option(idx2 + 1, value=idx2) for idx2 in xrange(0, len(answers))],
                                       id='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(answer, 'value')),
                                       name='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(answer, 'value'))),
                            tag.label(get_qg_attr_value(answer, 'label'), for_='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(answer, 'value'))),
                            id='items.%s.%s.%s-item' % (item['did'], question.name, get_qg_attr_value(answer, 'value'))))
    shuffle(items)
    return form.error_wrapper(tag.ul(items), 'items.%s.%s' % (item['did'], question.name), e)
