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

def checkbox(name, value, options, e, **attr):
    if value == options[0]:
        attr['checked'] = 'checked'
    elif value == options[1]:
        if 'checked' in attr:
            del attr['checked']
    return tag(hidden_field(name, options[1]),
               error_wrapper(tag.input(type='checkbox', name=name, **attr), name, e))

def textarea(name, text, e, **attr):
    return error_wrapper(tag.textarea(text, name=name, **attr), name, e)

def button(label, **attr):
    return tag.input(type='button', value=label, **attr)

def submit(label, **attr):
    return tag.input(type='submit', value=label, **attr)
