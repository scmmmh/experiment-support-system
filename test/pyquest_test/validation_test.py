# -*- coding: utf-8 -*-
'''
Created on 3 Feb 2012

@author: mhall
'''
from formencode import Invalid
from nose.tools import eq_, assert_raises
from webob.multidict import MultiDict

from pyquest.validation import *
    
def page_schema_test():
    schema = {'type': 'compound', 'fields': {'name': {'type': 'unicode',
                                                      'required': True},
                                             'email': {'type': 'email',
                                                       'required': True},
                                             'homepage': {'type': 'url',
                                                          'required': True}}}
    submission = MultiDict([('items.1.name', 'Mark'),
                            ('items.1.email', 'somebody@somewhere.com'),
                            ('items.1.homepage', 'http://www.example.com')])
    eq_({'items': {'1': {'name': 'Mark', 'email': 'somebody@somewhere.com', 'homepage': 'http://www.example.com'}}},
        PageSchema(schema, [{'did': 1}]).to_python(submission))
    submission = MultiDict([('items.1.name', ''),
                            ('items.1.email', 'somebody@somewhere.com'),
                            ('items.1.homepage', 'http://www.example.com')])
    assert_raises(Invalid, PageSchema(schema, [{'did': 1}]).to_python, submission)
    submission = MultiDict([('items.1.name', 'Mark'),
                            ('items.1.email', ''),
                            ('items.1.homepage', 'http://www.example.com')])
    assert_raises(Invalid, PageSchema(schema, [{'did': 1}]).to_python, submission)
    submission = MultiDict([('items.1.name', 'Mark'),
                            ('items.1.email', 'somebody@somewhere.com'),
                            ('items.1.homepage', '')])
    assert_raises(Invalid, PageSchema(schema, [{'did': 1}]).to_python, submission)
    submission = MultiDict([('items.1.email', 'somebody@somewhere.com'),
                            ('items.1.homepage', 'http://www.example.com')])
    assert_raises(Invalid, PageSchema(schema, [{'did': 1}]).to_python, submission)

def number_input_test():
    """Tests that the number element is generated correctly."""
    schema = qsheet_to_schema('<pq:number name="number" title="Specify a number, ${name}" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"></pq:number>')
    eq_({'number': {'type': 'number', 'required': True}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.number', '4')]))
    schema = qsheet_to_schema('<pq:number name="number" title="Specify a number, ${name}" min_value="2" max_value="6" step="2" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"></pq:number>')
    eq_({'number': {'type': 'number', 'min_value': 2, 'max_value': 6, 'step': 2}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.number', '4')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.number', '2')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.number', '6')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.number', '1')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.number', '9')]))
    schema = qsheet_to_schema('<pq:number name="number" required="true" title="Specify a number, ${name}" min_value="2" max_value="4" step="${step}" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"></pq:number>')
    eq_({'number': {'type': 'number', 'min_value': 2, 'max_value': 4, 'required': True}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.number', '4')]))

def email_input_test():
    """Tests that the e-mail element is generated correctly."""
    schema = qsheet_to_schema('<pq:email name="email" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'email': {'type': 'email', 'required': True}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.email', 'somebody@example.com')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.email', 'somebody.somewhere')]))

def url_input_test():
    """Tests that the url element is generated correctly."""
    schema = qsheet_to_schema('<pq:url name="url" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'url': {'type': 'url', 'required': True}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.url', 'http://example.com/home/~username?yes=q')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.url', 'Nothing')]))

def date_input_test():
    """Tests that the date element is generated correctly."""
    schema = qsheet_to_schema('<pq:date name="birthday" title="Please provide your birthday" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'birthday': {'type': 'date', 'required': True}},
        schema)

def time_input_test():
    """Tests that the time element is generated correctly."""
    schema = qsheet_to_schema('<pq:time name="time" title="Please provide the current time" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'time': {'type': 'time', 'required': True}},
        schema)

def datetime_input_test():
    """Tests that the datetime element is generated correctly."""
    schema = qsheet_to_schema('<pq:datetime name="now" title="Please provide the current date and time" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'now': {'type': 'datetime', 'required': True}},
        schema)

def month_input_test():
    """Tests that the datetime element is generated correctly."""
    schema = qsheet_to_schema('<pq:month name="month" title="Please provide the current month" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'month': {'type': 'month', 'required': True}},
        schema)

def short_text_input_test():
    """Tests that the text element is generated correctly."""
    schema = qsheet_to_schema('<pq:short_text name="name" title="What is your name?" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'name': {'type': 'unicode', 'required': True}},
        schema)

def long_text_input_test():
    """Tests that the textarea element is generated correctly."""
    schema = qsheet_to_schema('<pq:long_text name="description" title="Briefly describe yourself" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'description': {'type': 'unicode', 'required': True}},
        schema)

def rating_test():
    """Tests that the rating element is generated correctly."""
    schema = qsheet_to_schema('<pq:rating name="rating" title="Rate this" min_value="1" min_title="First" max_value="3" max_title="Last" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'rating': {'type': 'single_in_list', 'values': ['1', '2', '3']}},
        schema)
    schema = qsheet_to_schema('<pq:rating name="rating" title="Rate this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2"/><pq:option value="3" title="Last"/></pq:rating>')
    eq_({'rating': {'type': 'single_in_list', 'values': ['1', '2', '3']}},
        schema)

def rating_group_test():
    """Tests that the rating element is generated correctly."""
    schema = qsheet_to_schema('<pq:rating_group name="rating" title="Rate this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2"/><pq:option value="3" title="Last"/><pq:rating name="q1" title="Question 1"/><pq:rating name="q2" title="Question 2"/></pq:rating_group>')
    eq_({'rating': {'type': 'compound',
                    'fields': {'q1': {'type': 'single_in_list', 'values': ['1', '2', '3']},
                               'q2': {'type': 'single_in_list', 'values': ['1', '2', '3']}}}},
        schema)

def listchoice_test():
    """Tests that the listchoice element is generated correctly."""
    schema = qsheet_to_schema('<pq:listchoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1"/><pq:option value="2"/><pq:option value="3"/></pq:listchoice>')
    eq_({'choose': {'type': 'single_in_list', 'values': ['1', '2', '3']}},
        schema)

def selectchoice_test():
    """Tests that the selectchoice element is generated correctly."""
    schema = qsheet_to_schema('<pq:selectchoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/></pq:selectchoice>')
    eq_({'choose': {'type': 'single_in_list', 'values': ['1', '2', '3']}},
        schema)

def multichoice_test():
    """Tests that the multichoice element is generated correctly."""
    schema = qsheet_to_schema('<pq:multichoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1"/><pq:option value="2"/><pq:option value="3"/></pq:multichoice>')
    eq_({'choose': {'type': 'multi_in_list', 'values': ['1', '2', '3']}},
        schema)

def multichoice_group_test():
    """Tests that the multichoice_gorup element is generated correctly."""
    schema = qsheet_to_schema('<pq:multichoice_group name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/><pq:multichoice name="q1" title="Question 1"/><pq:multichoice name="q2" title="Question 2"/></pq:multichoice_group>')
    eq_({'choose': {'type': 'compound',
                    'fields': {'q1': {'type': 'multi_in_list', 'values': ['1', '2', '3']},
                               'q2': {'type': 'multi_in_list', 'values': ['1', '2', '3']}}}},
        schema)

def confirm_test():
    """Tests that the confirmation element is generated corrrectly."""
    schema = qsheet_to_schema('<pq:confirm name="confirmation" title="Please confirm this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'confirmation': {'type': 'boolean'}},
        schema)
    schema = qsheet_to_schema('<pq:confirm name="confirmation" required="true" title="Please confirm this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'confirmation': {'type': 'boolean',
                          'required': True}},
        schema)

def ranking_test():
    """Tests that the ranking element is generated correctly."""
    schema = qsheet_to_schema('<pq:ranking name="importance" title="Please rank the following items" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="cat" title="Cat"/><pq:option value="dog" title="Dog"/><pq:option value="mouse" title="Mouse"/></pq:ranking>')
    eq_({'importance': {'type': 'all_in_list', 'values': ['cat', 'dog', 'mouse']}},
        schema)
