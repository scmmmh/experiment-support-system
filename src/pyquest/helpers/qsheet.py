# -*- coding: utf-8 -*-
'''
Created on 20 Jan 2012

@author: mhall
'''
from re import search
from genshi.builder import tag
from lxml import etree
from StringIO import StringIO

def display(item, content):
    doc = etree.parse(StringIO('<pq:qsheet xmlns:pq="http://paths.sheffield.ac.uk/pyquest">%s</pq:qsheet>' % (content)))
    return process(doc.getroot(), item)

def substitute(text, item):
    if text:
        m = search('\${.+}', text)
        while(m):
            tag = m.group(0)[2:-1]
            if tag in item:
                text = text.replace(m.group(0), item[tag])
            else:
                text = text.replace(m.group(0), tag)
            m = search('\${.+}', text)
        return text
    else:
        return None

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
        return rating_input(element, item)
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

def add_title(element, tags):
    if 'title' in element.attrib:
        tags.append(tag.hgroup(tag.h1(element.attrib['title'])))

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
            values = [(idx, '') for idx in xrange(min_value + 1, max_value)]
        else:
            values = [(idx, str(idx)) for idx in xrange(min_value + 1, max_value)]
        values.insert(0, (min_value, min_title))
        values.append((max_value, max_title))
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
    
def number_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    attr = {'name': 'item-1.%s' % (element.attrib['name'])}
    if 'min_value' in element.attrib:
        attr['min'] = substitute(element.attrib['min_value'], item)
    if 'max_value' in element.attrib:
        attr['max'] = substitute(element.attrib['max_value'], item)
    if 'step' in element.attrib:
        attr['step'] = substitute(element.attrib['step'], item)
    tags.append(tag.input(type='number',
                          **attr))
    return tag.section(tags, class_='question number')

def email_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='email',
                          name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question email')
    
def url_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='url',
                          name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question url')
    
def date_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='date',
                          name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question url')

def time_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='time',
                          name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question time')
    
def datetime_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='datetime',
                          name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question datetime')
        
def month_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='month',
                          name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question month')

def short_text_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='text',
                          name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question short-text')

def long_text_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.textarea(name='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question long-text')

def rating_input(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    rows = []
    choices = extract_choices(element)
    rows.append(tag.thead(tag.tr(map(lambda (_, t): tag.th(t), choices))))
    rows.append(tag.tbody(tag.tr(map(lambda (v, _): tag.td(tag.input(type='radio',
                                                           name='item-1.%s' % (element.attrib['name']),
                                                           value=v)),
                           choices))))
    tags.append(tag.table(rows))
    return tag.section(tags, class_='question rating')

def rating_group(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    choices = extract_choices(element)
    rows = []
    for rating in element:
        if rating.tag == u'{http://paths.sheffield.ac.uk/pyquest}rating':
            if 'name' in rating.attrib:
                if 'title' in rating.attrib:
                    rows.append(tag.tr(tag.th(rating.attrib['title']),
                                       map(lambda (v, _): tag.td(tag.input(type='radio',
                                                                           name='item-1.%s.%s' % (element.attrib['name'], rating.attrib['name']),
                                                                           value=v)),
                                           choices)))
    tags.append(tag.table(tag.thead(tag.tr(tag.th(), map(lambda (_, t): tag.th(t), choices))),
                          tag.tbody(rows)))
    return tag.section(tags, class_='question rating-group')

def listchoice(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    list = []
    for idx, (value, title) in enumerate(extract_choices(element)):
        list.append(tag.li(tag.input(type='radio', id='item-1.%s-%i' % (element.attrib['name'], idx), name='item-1.%s' % (element.attrib['name']), value=value),
                           tag.label(title, for_='item-1.%s-%i' % (element.attrib['name'], idx))))
    tags.append(tag.ul(list))
    return tag.section(tags, class_='question listchoice')

def selectchoice(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    choices = map(lambda (v, t): tag.option(t, value=v), extract_choices(element))
    choices.insert(0, tag.option('--- Please choose ---', value='--no-choice--'))
    tags.append(tag.select(choices, name=element.attrib['name']))
    return tag.section(tags, class_='question selectchoice')

def multichoice(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    choices = extract_choices(element)
    items = []
    for idx, (v, t) in enumerate(choices):
        item = []
        item.append(tag.input(type='checkbox', id='item-1.%s-%i' % (element.attrib['name'], idx), name='item-1.%s-%i' % (element.attrib['name'], idx), value=v))
        if t != '':
            item.append(tag.label(t, for_='item-1.%s-%i' % (element.attrib['name'], idx)))
        items.append(tag.li(item))
    tags.append(tag.ul(items))
    return tag.section(tags, class_='question multichoice')

def multichoice_group(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
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
                for idx, (v, _) in enumerate(choices):
                    columns.append(tag.td(tag.input(type='checkbox', id='item-1.%s-%i' % (element.attrib['name'], idx), name='item-1.%s-%i' % (element.attrib['name'], idx), value=v)))
                rows.append(tag.tr(columns))
    tags.append(tag.table(tag.thead(tag.tr(tag.th(''), map(lambda (_, t): tag.th(t), choices))),
                          tag.tbody(rows)))
    return tag.section(tags, class_='question multichoice-grid')

def confirm(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    tags.append(tag.input(type='hidden', name='item-1.%s' % (element.attrib['name']), value='false'))
    tags.append(tag.input(type='checkbox', id='item-1.%s' % (element.attrib['name']), name='item-1.%s' % (element.attrib['name']), value='true'))
    if 'title' in element.attrib:
        tags.append(tag.label(element.attrib['title'], for_='item-1.%s' % (element.attrib['name'])))
    return tag.section(tags, class_='question confirm')
    
def ranking(element, item):
    if 'name' not in element.attrib:
        return None
    tags = []
    add_title(element, tags)
    choices = extract_choices(element)
    items = []
    for value, title in choices:
        items.append(tag.li(tag.select([tag.option(idx2 + 1, value=idx2) for idx2 in xrange(0, len(choices))], id='item-1.%s.%s' % (element.attrib['name'], value), name='item-1.%s.%s' % (element.attrib['name'], value)),
                            tag.label(title, for_='item-1.%s.%s' % (element.attrib['name'], value))))
    tags.append(tag.ul(items))
    return tag.section(tags, class_='question ranking')
