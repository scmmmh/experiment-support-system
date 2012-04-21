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

def get_qs_attr(qsheet, key, default=None):
    for attr in qsheet.attributes:
        if attr.key == key:
            return attr
    return default

def get_qs_attr_value(qsheet, key, default=None):
    attr = get_qs_attr(qsheet, key, default)
    if attr:
        if attr.value:
            return attr.value
        else:
            return default
    else:
        return default
    
def get_qg_attr(attr_group, key, default=None):
    for attr in attr_group.attributes:
        if attr.key == key:
            return attr
    return default

def get_qg_attr_value(attr_group, key, default=None):
    attr = get_qg_attr(attr_group, key, default)
    if attr:
        if attr.value:
            return attr.value
        else:
            return default
    else:
        return default
    
def get_q_attr(question, key, default=None):
    keys = key.split('.')
    if len(keys) < 2:
        return default
    for attr_group in question.attributes:
        if attr_group.key == keys[0]:
            return get_qg_attr(attr_group, keys[1], default)
    return default
    
def get_q_attr_value(question, key, default=None):
    attr = get_q_attr(question, key, default)
    if attr:
        if attr.value:
            return attr.value
        else:
            return default
    else:
        return default
    
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
    elif q_type == 'single_choice':
        return 'Single choice'
    elif q_type == 'multi_choice':
        return 'Multiple choice'
    elif q_type == 'rating_group':
        return 'Rating grid'
    elif q_type == 'confirm':
        return 'Confirmation checkbox'
    elif q_type == 'multichoice_group':
        return 'Multiple choice grid'
    elif q_type == 'ranking':
        return 'Ranking'
    else:
        return q_type
    
def substitute(text, item):
    if text:
        m = search('\${.+?}', text)
        while(m):
            tag = m.group(0)[2:-1]
            if tag in item:
                text = text.replace(m.group(0), unicode(item[tag]))
            else:
                text = text.replace(m.group(0), tag)
            m = search('\${.+?}', text)
        return text
    else:
        return None

def display(question, item, e, csrf_token=None):
    if question.type == 'text':
        return tag.section(Markup(substitute(get_q_attr_value(question, 'text.text'), item)))
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
    elif question.type == 'single_choice':
        subtype = get_q_attr_value(question, 'further.subtype', 'table')
        if subtype == 'table':
            return single_table(question, item, e)
        elif subtype == 'list':
            return single_list(question, item, e)
        elif subtype == 'select':
            return single_select(question, item, e)
    elif question.type == 'rating_group':
        return rating_group(question, item, e)
    elif question.type == 'confirm':
        return confirm(question, item, e)
    elif question.type == 'multi_choice':
        return multi_choice(question, item, e)
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
    min_value = get_q_attr_value(question, 'further.min')
    if min_value and min_value.strip() != '':
        attr['min'] = substitute(get_q_attr_value(question, 'further.min'), item)
    max_value = get_q_attr_value(question, 'further.max')
    if max_value and max_value.strip() != '':
        attr['max'] = substitute(get_q_attr_value(question, 'further.min'), item)
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
def single_table(question, item, e):
    rows = []
    answers = get_attr_groups(question, 'answer')
    rows.append(tag.thead(tag.tr(map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers))))
    rows.append(tag.tbody(tag.tr(map(lambda a: tag.td(tag.input(type='radio',
                                                                name='items.%s.%s' % (item['did'], question.name),
                                                                value=get_qg_attr_value(a, 'value'))),
                                     answers))))
    return form.error_wrapper(tag.table(rows), 'items.%s.%s' % (item['did'], question.name), e)

@question()
def single_list(question, item, e):
    items = []
    answers = get_attr_groups(question, 'answer')
    for idx, answer in enumerate(answers):
        parts = [tag.input(type='radio',
                           id='items.%s.%s-%i' % (item['did'], question.name, idx),
                           name='items.%s.%s' % (item['did'], question.name),
                           value=get_qg_attr_value(answer, 'value'))]
        parts.append(tag.label(get_qg_attr_value(answer, 'label'),
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
def multi_choice(question, item, e):
    rows = []
    answers = get_attr_groups(question, 'answer')
    rows.append(tag.thead(tag.tr(map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers))))
    rows.append(tag.tbody(tag.tr(map(lambda a: tag.td(tag.input(type='checkbox',
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

def as_text(qsheet, as_markup=False, no_ids=False):
    def std_attr(question, no_id=False):
        if no_id:
            return 'name="%s" title="%s" help="%s"' % (question.name, question.title, question.help)
        else:
            return 'id="%i" name="%s" title="%s" help="%s"' % (question.id, question.name, question.title, question.help)
    def to_text(question, no_id):
        if question.type == 'text':
            if no_id:
                return '<pq:static_text>%s</pq:static_text>' % (get_q_attr_value(question, 'text.text'))
            else:
                return '<pq:static_text id="%i">%s</pq:static_text>' % (question.id, get_q_attr_value(question, 'text.text'))
        elif question.type == 'short_text':
            return '<pq:short_text %s/>' % (std_attr(question, no_id))
        elif question.type == 'long_text':
            return '<pq:long_text %s/>' % (std_attr(question, no_id))
        elif question.type == 'number':
            return '<pq:number %s min="%s" max="%s"/>' % (std_attr(question, no_id), get_q_attr_value(question, 'further.min', ''), get_q_attr_value(question, 'further.max', ''))
        elif question.type == 'email':
            return '<pq:email %s/>' % (std_attr(question, no_id))
        elif question.type == 'url':
            return '<pq:url %s/>' % (std_attr(question, no_id))
        elif question.type == 'date':
            return '<pq:date %s/>' % (std_attr(question, no_id))
        elif question.type == 'time':
            return '<pq:time %s/>' % (std_attr(question, no_id))
        elif question.type == 'datetime':
            return '<pq:datetime %s/>' % (std_attr(question, no_id))
        elif question.type == 'month':
            return '<pq:month %s/>' % (std_attr(question, no_id))
        elif question.type == 'single_choice':
            lines = ['<pq:single_choice %s display="%s">' % (std_attr(question, no_id), get_q_attr_value(question, 'further.subtype', 'table'))]
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label', '')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:single_choice>')
            return u'\n'.join(lines) 
        elif question.type == 'multi_choice':
            lines = ['<pq:multi_choice %s>' % (std_attr(question, no_id))]
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label', '')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:multi_choice>')
            return u'\n'.join(lines) 
        elif question.type == 'rating_group':
            lines = ['<pq:rating_group %s>' % (std_attr(question, no_id))]
            lines.extend(['  <pq:sub_question name="%s" label="%s"/>' % (get_qg_attr_value(qg, 'name'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'subquestion')])
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:rating_group>')
            return u'\n'.join(lines)
        elif question.type == 'confirm':
            return '<pq:confirm %s value="%s" label="%s"/>' % (std_attr(question, no_id), get_q_attr_value(question, 'further.value', ''), get_q_attr_value(question, 'further.label', ''))
        elif question.type == 'multichoice_group':
            lines = ['<pq:multichoice_group %s>' % (std_attr(question, no_id))]
            lines.extend(['  <pq:sub_question name="%s" label="%s"/>' % (get_qg_attr_value(qg, 'name'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'subquestion')])
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:multichoice_group>')
            return u'\n'.join(lines)
        elif question.type == 'ranking':
            lines = ['<pq:ranking %s>' % (std_attr(question, no_id))]
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:ranking>')
            return u'\n'.join(lines) 
        else:
            return ''
    
    if as_markup:
        return Markup('\n'.join([to_text(q, no_ids) for q in qsheet.questions]))
    else:
        return '\n'.join([to_text(q, no_ids) for q in qsheet.questions])
