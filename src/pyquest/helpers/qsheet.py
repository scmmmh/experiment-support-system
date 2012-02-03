# -*- coding: utf-8 -*-
'''
Created on 20 Jan 2012

@author: mhall
'''
from decorator import decorator
from genshi.builder import tag
from lxml import etree
from re import search
from StringIO import StringIO

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

def question(question_type):
    def wrapper(f, element, item):
        if 'name' not in element.attrib:
            return None
        tags = f(element, item)
        if not isinstance(tags, list):
            tags = [tags]
        if 'title' in element.attrib:
            tags.insert(0, tag.hgroup(tag.h1(substitute(element.attrib['title'], item))))
        return tag.section(tags, class_='question %s' % (question_type))
    return decorator(wrapper)

def extract_choices(element):
    if len(element) == 0:
        min_value = 1
        if 'min_value' in element.attrib:
            min_value = int(element.attrib['min_value'])
        min_title = '1'
        if 'min_title' in element.attrib:
            min_title = element.attrib['min_title']
        max_value = 5
        if 'max_value' in element.attrib:
            max_value = int(element.attrib['max_value'])
        max_title ='5'
        if 'max_title' in element.attrib:
            max_title = element.attrib['max_title']
        if 'hide_extra_labels' in element.attrib and element.attrib['hide_extra_labels'].lower().strip() == 'true':
            element.attrib['hide_extra_labels']
            values = [(str(idx), '') for idx in xrange(min_value + 1, max_value)]
        else:
            values = [(str(idx), str(idx)) for idx in xrange(min_value + 1, max_value)]
        values.insert(0, (str(min_value), min_title))
        values.append((str(max_value), max_title))
        return values
    else:
        values = []
        for option in element:
            if option.tag == u'{http://paths.sheffield.ac.uk/pyquest}option':
                if 'value' in option.attrib:
                    if 'title' in option.attrib:
                        values.append((option.attrib['value'], option.attrib['title']))
                    else:
                        values.append((option.attrib['value'], ''))
        return values

def display(item, content):
    doc = etree.parse(StringIO('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % (content)))
    return process(doc.getroot(), item)

def process(element, item):
    if element.tag == u'{http://paths.sheffield.ac.uk/pyquest}qsheet':
        children = [element.text]
        for child in element:
            children.append(process(child, item))
            children.append(child.tail)
        return tag.section(children, class_='data-item')
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}number':
        return number_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}email':
        return email_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}url':
        return url_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}date':
        return date_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}time':
        return time_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}datetime':
        return datetime_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}month':
        return month_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}short_text':
        return short_text_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}long_text':
        return long_text_input(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}rating':
        return rating(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}rating_group':
        return rating_group(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}listchoice':
        return listchoice(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}selectchoice':
        return selectchoice(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}multichoice':
        return multichoice(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}multichoice_group':
        return multichoice_group(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}confirm':
        return confirm(element, item)
    elif element.tag == u'{http://paths.sheffield.ac.uk/pyquest}ranking':
        return ranking(element, item)
    else:
        children = [substitute(element.text, item)]
        for child in element:
            children.append(process(child, item))
            children.append(substitute(child.tail, item))
        attr = {}
        for (key, value) in element.attrib.items():
            attr[key] = substitute(value, item)
        return tag.__getattr__(element.tag)(children, **attr)

@question('number')    
def number_input(element, item):
    attr = {'name': 'items.%i.%s' % (item['did'], element.attrib['name'])}
    if 'min_value' in element.attrib:
        attr['min'] = substitute(element.attrib['min_value'], item)
    if 'max_value' in element.attrib:
        attr['max'] = substitute(element.attrib['max_value'], item)
    if 'step' in element.attrib:
        attr['step'] = substitute(element.attrib['step'], item)
    return tag.input(type='number', **attr)

@question('email')
def email_input(element, item):
    return tag.input(type='email',
                     name='items.%i.%s' % (item['did'], element.attrib['name']))
    
@question('url')
def url_input(element, item):
    return tag.input(type='url',
                     name='items.%i.%s' % (item['did'], element.attrib['name']))

@question('date')
def date_input(element, item):
    return tag.input(type='date',
                     name='items.%i.%s' % (item['did'], element.attrib['name']))

@question('time')
def time_input(element, item):
    return tag.input(type='time',
                     name='items.%i.%s' % (item['did'], element.attrib['name']))

@question('datetime')
def datetime_input(element, item):
    return tag.input(type='datetime',
                     name='items.%i.%s' % (item['did'], element.attrib['name']))
        
@question('month')
def month_input(element, item):
    return tag.input(type='month',
                     name='items.%i.%s' % (item['did'], element.attrib['name']))

@question('short_text')
def short_text_input(element, item):
    return tag.input(type='text',
                     name='items.%i.%s' % (item['did'], element.attrib['name']))

@question('long_text')
def long_text_input(element, item):
    return tag.textarea(name='items.%i.%s' % (item['did'], element.attrib['name']))

@question('rating')
def rating(element, item):
    rows = []
    choices = extract_choices(element)
    rows.append(tag.thead(tag.tr(map(lambda (_, t): tag.th(t), choices))))
    rows.append(tag.tbody(tag.tr(map(lambda (v, _): tag.td(tag.input(type='radio',
                                                                     name='items.%i.%s' % (item['did'], element.attrib['name']),
                                                                     value=v)),
                                     choices))))
    return tag.table(rows)

@question('rating_group')
def rating_group(element, item):
    choices = extract_choices(element)
    rows = []
    for rating in element:
        if rating.tag == u'{http://paths.sheffield.ac.uk/pyquest}rating':
            if 'name' in rating.attrib:
                if 'title' in rating.attrib:
                    rows.append(tag.tr(tag.th(rating.attrib['title']),
                                       map(lambda (v, _): tag.td(tag.input(type='radio',
                                                                           name='items.%i.%s.%s' % (item['did'], element.attrib['name'], rating.attrib['name']),
                                                                           value=v)),
                                           choices)))
    return tag.table(tag.thead(tag.tr(tag.th(), map(lambda (_, t): tag.th(t), choices))),
                     tag.tbody(rows))

@question('listchoice')
def listchoice(element, item):
    items = []
    for idx, (value, title) in enumerate(extract_choices(element)):
        parts = [tag.input(type='radio',
                           id='items.%i.%s-%i' % (item['did'], element.attrib['name'], idx),
                           name='items.%i.%s' % (item['did'], element.attrib['name']),
                           value=value)]
        if title != '':
            parts.append(tag.label(title,
                                   for_='items.%i.%s-%i' % (item['did'], element.attrib['name'], idx)))
        items.append(tag.li(parts))
    return tag.ul(items)

@question('selectchoice')
def selectchoice(element, item):
    choices = map(lambda (v, t): tag.option(t, value=v), extract_choices(element))
    choices.insert(0, tag.option('--- Please choose ---', value='--no-choice--'))
    return tag.select(choices,
                      name='items.%i.%s' % (item['did'], element.attrib['name']))

@question('multichoice')
def multichoice(element, item):
    choices = extract_choices(element)
    items = []
    for idx, (value, title) in enumerate(choices):
        list_item = []
        list_item.append(tag.input(type='checkbox',
                                   id='items.%i.%s-%i' % (item['did'], element.attrib['name'], idx),
                                   name='items.%i.%s' % (item['did'], element.attrib['name']),
                                   value=value))
        if title != '':
            list_item.append(tag.label(title, for_='items.%i.%s-%i' % (item['did'], element.attrib['name'], idx)))
        items.append(tag.li(list_item))
    return tag.ul(items)

@question('multichoice_group')
def multichoice_group(element, item):
    rows = []
    choices = extract_choices(element)
    for choice in element:
        if choice.tag == u'{http://paths.sheffield.ac.uk/pyquest}multichoice':
            if 'name' in element.attrib:
                columns = []
                if 'title' in choice.attrib:
                    columns.append(tag.th(choice.attrib['title']))
                else:
                    columns.append(tag.th())
                for (v, _) in choices:
                    columns.append(tag.td(tag.input(type='checkbox',
                                                    name='items.%i.%s.%s' % (item['did'], element.attrib['name'], choice.attrib['name']),
                                                    value=v)))
                rows.append(tag.tr(columns))
    return tag.table(tag.thead(tag.tr(tag.th(''), map(lambda (_, t): tag.th(t), choices))),
                          tag.tbody(rows))

@question('confirm')
def confirm(element, item):
    tags = []
    tags.append(tag.input(type='checkbox',
                          id='items.%i.%s' % (item['did'], element.attrib['name']),
                          name='items.%i.%s' % (item['did'], element.attrib['name']),
                          value='true'))
    if 'label' in element.attrib:
        tags.append(tag.label(element.attrib['label'],
                              for_='items.%i.%s' % (item['did'], element.attrib['name'])))
    elif 'title' in element.attrib:
        tags.append(tag.label(element.attrib['title'],
                              for_='items.%i.%s' % (item['did'], element.attrib['name'])))
    return tag(tags)
    
@question('ranking')
def ranking(element, item):
    choices = extract_choices(element)
    items = []
    for value, title in choices:
        items.append(tag.li(tag.select(tag.option('--', value='--no-choice--'),
                                       [tag.option(idx2 + 1, value=idx2) for idx2 in xrange(0, len(choices))],
                                       id='items.%i.%s.%s' % (item['did'], element.attrib['name'], value),
                                       name='items.%i.%s.%s' % (item['did'], element.attrib['name'], value)),
                            tag.label(title, for_='items.%i.%s.%s' % (item['did'], element.attrib['name'], value))))
    return tag.ul(items)
