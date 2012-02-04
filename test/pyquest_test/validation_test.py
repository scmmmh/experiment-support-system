# -*- coding: utf-8 -*-
'''
Created on 3 Feb 2012

@author: mhall
'''
import datetime

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
    eq_({'items': {'1': {'birthday': datetime.date(1964, 2, 29)}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.birthday', '29/02/1964')])))
    eq_({'items': {'1': {'birthday': datetime.date(1964, 2, 29)}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.birthday', '29/2/1964')])))
    eq_({'items': {'1': {'birthday': datetime.date(1964, 2, 2)}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.birthday', '2/2/1964')])))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.birthday', '29/13/1967')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.birthday', '29/02/1967')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.birthday', 'Something')]))

def time_input_test():
    """Tests that the time element is generated correctly."""
    schema = qsheet_to_schema('<pq:time name="time" title="Please provide the current time" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'time': {'type': 'time', 'required': True}},
        schema)
    eq_({'items': {'1': {'time': datetime.time(14, 32)}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.time', '14:32')])))
    eq_({'items': {'1': {'time': datetime.time(4, 32)}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.time', '4:32')])))
    eq_({'items': {'1': {'time': datetime.time(12, 3)}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.time', '12:3')])))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.time', '26:12')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.time', '12:65')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.time', 'Something')]))

def datetime_input_test():
    """Tests that the datetime element is generated correctly."""
    schema = qsheet_to_schema('<pq:datetime name="now" title="Please provide the current date and time" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'now': {'type': 'datetime', 'required': True}},
        schema)
    eq_({'items': {'1': {'now': datetime.datetime(1964, 2, 29, 14, 32)}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.now', '29/02/1964 14:32')])))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.now', '29/02/1967 13:12')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.now', '29/02/1968 27:12')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.now', 'Something')]))

def month_input_test():
    """Tests that the datetime element is generated correctly."""
    schema = qsheet_to_schema('<pq:month name="month" title="Please provide the current month" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'month': {'type': 'month', 'required': True}},
        schema)
    eq_({'items': {'1': {'month': 4}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.month', '4')])))
    eq_({'items': {'1': {'month': 4}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.month', 'apr')])))
    eq_({'items': {'1': {'month': 4}}},
         PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.month', 'april')])))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.month', '13')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.month', 'frank')]))

def short_text_input_test():
    """Tests that the text element is generated correctly."""
    schema = qsheet_to_schema('<pq:short_text name="name" title="What is your name?" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'name': {'type': 'unicode', 'required': True}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.name', 'Sir Lancelot')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.name', '')]))

def long_text_input_test():
    """Tests that the textarea element is generated correctly."""
    schema = qsheet_to_schema('<pq:long_text name="description" title="Briefly describe yourself" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'description': {'type': 'unicode', 'required': True}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.description', 'I am a knight of the round table')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.name', '')]))

def rating_test():
    """Tests that the rating element is generated correctly."""
    schema = qsheet_to_schema('<pq:rating name="rating" title="Rate this" min_value="1" min_title="First" max_value="3" max_title="Last" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'rating': {'type': 'single_in_list', 'values': ['1', '2', '3']}},
        schema)
    schema = qsheet_to_schema('<pq:rating name="rating" title="Rate this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2"/><pq:option value="3" title="Last"/></pq:rating>')
    eq_({'rating': {'type': 'single_in_list', 'values': ['1', '2', '3']}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.rating', '2')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.rating', '2'), ('items.1.rating', '3')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.rating', '0')]))

def rating_group_test():
    """Tests that the rating element is generated correctly."""
    schema = qsheet_to_schema('<pq:rating_group name="rating" title="Rate this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2"/><pq:option value="3" title="Last"/><pq:rating name="q1" title="Question 1"/><pq:rating name="q2" title="Question 2"/></pq:rating_group>')
    eq_({'rating': {'type': 'compound',
                    'fields': {'q1': {'type': 'single_in_list', 'values': ['1', '2', '3']},
                               'q2': {'type': 'single_in_list', 'values': ['1', '2', '3']}}}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.rating.q1', '2')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.rating.q1', '2'), ('items.1.rating.q2', '1')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.rating', '2'), ('items.1.rating', '3')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.rating', '0')]))
    schema = qsheet_to_schema('<pq:rating_group name="rating" title="Rate this" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2"/><pq:option value="3" title="Last"/><pq:rating name="q1" title="Question 1"/><pq:rating name="q2" title="Question 2"/></pq:rating_group>')
    eq_({'rating': {'type': 'compound',
                    'fields': {'q1': {'type': 'single_in_list', 'values': ['1', '2', '3'], 'required': True},
                               'q2': {'type': 'single_in_list', 'values': ['1', '2', '3'], 'required': True}},
                    'required': True}},
        schema)
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.rating.q1', '2')]))

def listchoice_test():
    """Tests that the listchoice element is generated correctly."""
    schema = qsheet_to_schema('<pq:listchoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1"/><pq:option value="2"/><pq:option value="3"/></pq:listchoice>')
    eq_({'choose': {'type': 'single_in_list', 'values': ['1', '2', '3']}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose', '2')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose', '')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.choose', '2'), ('items.1.choose', '3')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.choose', '0')]))

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
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose', '2')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose', '2'), ('items.1.choose', '3')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose', '')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1', '')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.choose', '2'), ('items.1.choose', '4')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.choose', '0')]))

def multichoice_group_test():
    """Tests that the multichoice_gorup element is generated correctly."""
    schema = qsheet_to_schema('<pq:multichoice_group name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/><pq:multichoice name="q1" title="Question 1"/><pq:multichoice name="q2" title="Question 2"/></pq:multichoice_group>')
    eq_({'choose': {'type': 'compound',
                    'fields': {'q1': {'type': 'multi_in_list', 'values': ['1', '2', '3']},
                               'q2': {'type': 'multi_in_list', 'values': ['1', '2', '3']}}}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose.q1', '2')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose.q1', '2'), ('items.1.choose.q1', '3'), ('items.1.choose.q2', '3'), ('items.1.choose.q2', '1')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose.q1', '')]))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1', '')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.choose.q1', '2'), ('items.1.choose.q1', '4')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.choose.q1', '1'), ('items.1.choose.q2', '0')]))
    schema = qsheet_to_schema('<pq:multichoice_group name="choose" title="Please choose" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/><pq:multichoice name="q1" title="Question 1"/><pq:multichoice name="q2" title="Question 2"/></pq:multichoice_group>')
    eq_({'choose': {'type': 'compound',
                    'fields': {'q1': {'type': 'multi_in_list', 'values': ['1', '2', '3'], 'required': True},
                               'q2': {'type': 'multi_in_list', 'values': ['1', '2', '3'], 'required': True}},
                    'required': True}},
        schema)
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.choose.q1', '2'), ('items.1.choose.q1', '3'), ('items.1.choose.q2', '3'), ('items.1.choose.q2', '1')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.choose.q1', '2')]))

def confirm_test():
    """Tests that the confirmation element is generated corrrectly."""
    schema = qsheet_to_schema('<pq:confirm name="confirmation" title="Please confirm this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'confirmation': {'type': 'boolean'}},
        schema)
    eq_({'items': {'1': {'confirmation': True}}},
        PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.confirmation', 'true')])))
    eq_({'items': {'1': {'confirmation': False}}},
        PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1', '')])))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.confirmation', 'nonsense')]))
    schema = qsheet_to_schema('<pq:confirm name="confirmation" required="true" title="Please confirm this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    eq_({'confirmation': {'type': 'boolean',
                          'required': True}},
        schema)
    eq_({'items': {'1': {'confirmation': True}}},
        PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.confirmation', 'true')])))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.confirmation', '')]))

def ranking_test():
    """Tests that the ranking element is generated correctly."""
    schema = qsheet_to_schema('<pq:ranking name="importance" title="Please rank the following items" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="cat" title="Cat"/><pq:option value="dog" title="Dog"/><pq:option value="mouse" title="Mouse"/></pq:ranking>')
    eq_({'importance': {'type': 'all_in_list', 'values': ['cat', 'dog', 'mouse']}},
        schema)
    eq_({'items': {'1': {'importance': {'dog': 1, 'cat': 0, 'mouse': 2}}}},
        PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.importance.dog', '1'), ('items.1.importance.cat', '0'), ('items.1.importance.mouse', '2')])))
    PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.importance', '')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.importance.dog', '0'), ('items.1.importance.cat', '1')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.importance.dog', '0'), ('items.1.importance.cat', '1'), ('items.1.importance.cat', '3')]))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.importance.dog', '0'), ('items.1.importance.dog', '1'), ('items.1.importance.cat', '1'), ('items.1.importance.cat', '2')]))
    schema = qsheet_to_schema('<pq:ranking name="importance" title="Please rank the following items" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="cat" title="Cat"/></pq:ranking>')
    eq_({'importance': {'type': 'all_in_list', 'values': ['cat'], 'required': True}},
        schema)
    eq_({'items': {'1': {'importance': {'cat': 0}}}},
        PageSchema({'fields': schema}, [{'did': 1}]).to_python(MultiDict([('items.1.importance.cat', '0')])))
    assert_raises(Invalid, PageSchema({'fields': schema}, [{'did': 1}]).to_python, MultiDict([('items.1.importance.dog', '0')]))
