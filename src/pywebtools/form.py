# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
from genshi.builder import tag

def error_wrapper(content, field, e):
    if e and e.error_dict:
        if isinstance(field, list):
            for field in field:
                if field in e.error_dict:
                    return tag.div(content,
                                   tag.p(e.error_dict[field], class_='error-explanation'),
                                   class_="error")
            return content
        elif field in e.error_dict:
            return tag.div(content,
                           tag.p(e.error_dict[field], class_='error-explanation'),
                           class_="error")
        else:
            return content
    else:
        return content

def hidden_field(name, value, **attr):
    return tag.span(tag.input(type="hidden", name=name, value=value, **attr), style='display:none;')

def csrf_token(token):
    return hidden_field('csrf_token', token)

def text_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='text', name=name, value=text, **attr), name, e)

def number_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='number', name=name, value=text, **attr), name, e)

def email_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='email', name=name, value=text, **attr), name, e)

def url_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='url', name=name, value=text, **attr), name, e)

def date_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='date', name=name, value=text, **attr), name, e)

def time_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='time', name=name, value=text, **attr), name, e)

def datetime_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='datetime', name=name, value=text, **attr), name, e)

def month_field(name, text, e, **attr):
    return error_wrapper(tag.input(type='month', name=name, value=text, **attr), name, e)

def password_field(name, e, **attr):
    return error_wrapper(tag.input(type='password', name=name, **attr), name, e)

def file_input(name, e, **attr):
    return error_wrapper(tag.input(type='file', name=name, **attr), name, e)

def checkbox(name, value, e, checked=False, label=None, **attr):
    if checked:
        attr['checked'] = 'checked'
    else:
        if 'checked' in attr:
            del attr['checked']
    if label:
        if 'id' not in attr:
            attr['id'] = '%s.%s' % (name, value)
        return error_wrapper(tag(tag.input(type='checkbox', name=name, value=value, **attr),
                                 ' ', tag.label(label, for_=attr['id'])),
                             name, e)
    else:
        return error_wrapper(tag.input(type='checkbox', name=name, value=value, **attr), name, e)

def textarea(name, text, e, **attr):
    return error_wrapper(tag.textarea(text, name=name, **attr), name, e)

def select(name, value, options, e, **attr):
    select_options = []
    for option in options:
        if option[0] == value:
            select_options.append(tag.option(option[1], value=option[0], selected="selected"))
        else:
            select_options.append(tag.option(option[1], value=option[0]))
    return error_wrapper(tag.select(select_options, name=name, **attr), name, e)

def button(label, **attr):
    return tag.input(type='button', value=label, **attr)

def submit(label, **attr):
    return tag.input(type='submit', value=label, **attr)
