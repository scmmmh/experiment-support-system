# -*- coding: utf-8 -*-
'''
Test functions for the :mod:`pyquest.helpers.qsheet` module.

@author: Mark.Hall@work.room3b.eu
'''
from lxml.etree import fromstring
from nose.tools import eq_, ok_

from pyquest.helpers.qsheet import (substitute, extract_choices, number_input,
                                    email_input, url_input, date_input,
                                    time_input, datetime_input, month_input,
                                    short_text_input, long_text_input,
                                    single_table, rating_group, listchoice,
                                    selectchoice, multichoice, multichoice_group,
                                    confirm, ranking)

def substitute_test():
    eq_('Mark', substitute('Mark', {}))
    eq_('Mark', substitute('${name}', {'name': 'Mark'}))
    eq_('Hello Mark!', substitute('Hello ${name}!', {'name': 'Mark'}))
    eq_('Hello name!', substitute('Hello ${name}!', {}))
    eq_('I am 4 years old', substitute('I am ${nr} years old', {'nr': 4}))

def extract_choices_test():
    element = fromstring('<pq:single_table xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    choices = extract_choices(element)
    eq_(5, len(choices))
    eq_([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], choices)
    element = fromstring('<pq:single_table hide_extra_labels="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    choices = extract_choices(element)
    eq_(5, len(choices))
    eq_([('1', '1'), ('2', ''), ('3', ''), ('4', ''), ('5', '5')], choices)
    element = fromstring('<pq:single_table min_value="1" min_title="Not at all" max_value="9" max_title="Very" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    choices = extract_choices(element)
    eq_(9, len(choices))
    eq_([('1', 'Not at all'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', 'Very')], choices)
    element = fromstring('<pq:single_table xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="Not at all"/><pq:option value="2"/><pq:option value="3"/><pq:option value="4"/><pq:option value="5" title="Perfectly"/></pq:single_table>')
    choices = extract_choices(element)
    eq_(5, len(choices))
    eq_([('1', 'Not at all'), ('2', ''), ('3', ''), ('4', ''), ('5', 'Perfectly')], choices)

def no_name_test():
    """Tests that an element with no "name" attribute returns None."""
    element = fromstring('<pq:number xmlns:pq="http://paths.sheffield.ac.uk/pyquest"></pq:number>')
    ok_(not number_input(element, {'did': 1}, None))
    
def number_input_test():
    """Tests that the number element is generated correctly."""
    element = fromstring('<pq:number name="number" title="Specify a number, ${name}" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"></pq:number>')
    tags = number_input(element, {'did': 1, 'name': 'Mark'}, None)
    eq_('<section class="question number"><hgroup><h1>Specify a number, Mark</h1></hgroup><p><input type="number" name="items.1.number" value="" /></p></section>',
        tags.generate().render('xhtml'))
    element = fromstring('<pq:number name="number" title="Specify a number, ${name}" min_value="2" max_value="4" step="${step}" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"></pq:number>')
    tags = number_input(element, {'did': 1, 'name': 'Mark', 'step': 1}, None)
    eq_('<section class="question number"><hgroup><h1>Specify a number, Mark</h1></hgroup><p><input name="items.1.number" min="2" max="4" value="" step="1" type="number" /></p></section>',
        tags.generate().render('xhtml'))

def email_input_test():
    """Tests that the e-mail element is generated correctly."""
    element = fromstring('<pq:email name="email" title="Please provide your e-mail address" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = email_input(element, {'did': 1}, None)
    eq_('<section class="question email"><hgroup><h1>Please provide your e-mail address</h1></hgroup><p><input type="email" name="items.1.email" value="" /></p></section>',
        tags.generate().render('xhtml'))

def url_input_test():
    """Tests that the url element is generated correctly."""
    element = fromstring('<pq:url name="url" title="My homepage" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = url_input(element, {'did': 1}, None)
    eq_('<section class="question url"><hgroup><h1>My homepage</h1></hgroup><p><input type="url" name="items.1.url" value="" /></p></section>',
        tags.generate().render('xhtml'))

def date_input_test():
    """Tests that the date element is generated correctly."""
    element = fromstring('<pq:date name="birthday" title="Please provide your birthday" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = date_input(element, {'did': 1}, None)
    eq_('<section class="question date"><hgroup><h1>Please provide your birthday</h1></hgroup><p><input type="date" name="items.1.birthday" value="" /></p></section>',
        tags.generate().render('xhtml'))

def time_input_test():
    """Tests that the time element is generated correctly."""
    element = fromstring('<pq:time name="time" title="Please provide the current time" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = time_input(element, {'did': 1}, None)
    eq_('<section class="question time"><hgroup><h1>Please provide the current time</h1></hgroup><p><input type="time" name="items.1.time" value="" /></p></section>',
        tags.generate().render('xhtml'))

def datetime_input_test():
    """Tests that the datetime element is generated correctly."""
    element = fromstring('<pq:datetime name="now" title="Please provide the current date and time" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = datetime_input(element, {'did': 1}, None)
    eq_('<section class="question datetime"><hgroup><h1>Please provide the current date and time</h1></hgroup><p><input type="datetime" name="items.1.now" value="" /></p></section>',
        tags.generate().render('xhtml'))

def month_input_test():
    """Tests that the datetime element is generated correctly."""
    element = fromstring('<pq:month name="month" title="Please provide the current month" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = month_input(element, {'did': 1}, None)
    eq_('<section class="question month"><hgroup><h1>Please provide the current month</h1></hgroup><p><input type="month" name="items.1.month" value="" /></p></section>',
        tags.generate().render('xhtml'))

def short_text_input_test():
    """Tests that the text element is generated correctly."""
    element = fromstring('<pq:short_text name="name" title="What is your name?" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = short_text_input(element, {'did': 1}, None)
    eq_('<section class="question short_text"><hgroup><h1>What is your name?</h1></hgroup><p><input type="text" name="items.1.name" value="" /></p></section>',
        tags.generate().render('xhtml'))

def long_text_input_test():
    """Tests that the textarea element is generated correctly."""
    element = fromstring('<pq:long_text name="description" title="Briefly describe yourself" required="true" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = long_text_input(element, {'did': 1}, None)
    eq_('<section class="question long_text"><hgroup><h1>Briefly describe yourself</h1></hgroup><p><textarea name="items.1.description"></textarea></p></section>',
        tags.generate().render('xhtml'))

def rating_test():
    """Tests that the single_table element is generated correctly."""
    element = fromstring('<pq:single_table name="single_table" title="Rate this" min_value="1" min_title="First" max_value="3" max_title="Last" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = single_table(element, {'did': 1}, None)
    eq_('<section class="question single_table"><hgroup><h1>Rate this</h1></hgroup><table><thead><tr><th>First</th><th>2</th><th>Last</th></tr></thead><tbody><tr><td><input type="radio" name="items.1.single_table" value="1" /></td><td><input type="radio" name="items.1.single_table" value="2" /></td><td><input type="radio" name="items.1.single_table" value="3" /></td></tr></tbody></table></section>',
        tags.generate().render('xhtml'))
    element = fromstring('<pq:single_table name="single_table" title="Rate this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2"/><pq:option value="3" title="Last"/></pq:single_table>')
    tags = single_table(element, {'did': 1}, None)
    eq_('<section class="question single_table"><hgroup><h1>Rate this</h1></hgroup><table><thead><tr><th>First</th><th></th><th>Last</th></tr></thead><tbody><tr><td><input type="radio" name="items.1.single_table" value="1" /></td><td><input type="radio" name="items.1.single_table" value="2" /></td><td><input type="radio" name="items.1.single_table" value="3" /></td></tr></tbody></table></section>',
        tags.generate().render('xhtml'))

def rating_group_test():
    """Tests that the single_table element is generated correctly."""
    element = fromstring('<pq:rating_group name="single_table" title="Rate this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2"/><pq:option value="3" title="Last"/><pq:single_table name="q1" title="Question 1"/><pq:single_table name="q2" title="Question 2"/></pq:rating_group>')
    tags = rating_group(element, {'did': 1}, None)
    eq_('<section class="question rating_group"><hgroup><h1>Rate this</h1></hgroup><table><thead><tr><th></th><th>First</th><th></th><th>Last</th></tr></thead><tbody><tr><th>Question 1</th><td><input type="radio" name="items.1.single_table.q1" value="1" /></td><td><input type="radio" name="items.1.single_table.q1" value="2" /></td><td><input type="radio" name="items.1.single_table.q1" value="3" /></td></tr><tr><th>Question 2</th><td><input type="radio" name="items.1.single_table.q2" value="1" /></td><td><input type="radio" name="items.1.single_table.q2" value="2" /></td><td><input type="radio" name="items.1.single_table.q2" value="3" /></td></tr></tbody></table></section>',
        tags.generate().render('xhtml'))

def listchoice_test():
    """Tests that the listchoice element is generated correctly."""
    element = fromstring('<pq:listchoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1"/><pq:option value="2"/><pq:option value="3"/></pq:listchoice>')
    tags = listchoice(element, {'did': 1}, None)
    eq_('<section class="question listchoice"><hgroup><h1>Please choose</h1></hgroup><ul><li><input type="radio" name="items.1.choose" value="1" id="items.1.choose-0" /></li><li><input type="radio" name="items.1.choose" value="2" id="items.1.choose-1" /></li><li><input type="radio" name="items.1.choose" value="3" id="items.1.choose-2" /></li></ul></section>',
        tags.generate().render('xhtml'))
    element = fromstring('<pq:listchoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/></pq:listchoice>')
    tags = listchoice(element, {'did': 1}, None)
    eq_('<section class="question listchoice"><hgroup><h1>Please choose</h1></hgroup><ul><li><input type="radio" name="items.1.choose" value="1" id="items.1.choose-0" /><label for="items.1.choose-0">First</label></li><li><input type="radio" name="items.1.choose" value="2" id="items.1.choose-1" /><label for="items.1.choose-1">Middle</label></li><li><input type="radio" name="items.1.choose" value="3" id="items.1.choose-2" /><label for="items.1.choose-2">Last</label></li></ul></section>',
        tags.generate().render('xhtml'))

def selectchoice_test():
    """Tests that the selectchoice element is generated correctly."""
    element = fromstring('<pq:selectchoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/></pq:selectchoice>')
    tags = selectchoice(element, {'did': 1}, None)
    eq_('<section class="question selectchoice"><hgroup><h1>Please choose</h1></hgroup><p><select name="items.1.choose"><option value="">--- Please choose ---</option><option value="1">First</option><option value="2">Middle</option><option value="3">Last</option></select></p></section>',
        tags.generate().render('xhtml'))

def multichoice_test():
    """Tests that the multichoice element is generated correctly."""
    element = fromstring('<pq:multichoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1"/><pq:option value="2"/><pq:option value="3"/></pq:multichoice>')
    tags = multichoice(element, {'did': 1}, None)
    eq_('<section class="question multichoice"><hgroup><h1>Please choose</h1></hgroup><ul><li><input type="checkbox" name="items.1.choose" value="1" id="items.1.choose-0" /></li><li><input type="checkbox" name="items.1.choose" value="2" id="items.1.choose-1" /></li><li><input type="checkbox" name="items.1.choose" value="3" id="items.1.choose-2" /></li></ul></section>',
        tags.generate().render('xhtml'))
    element = fromstring('<pq:multichoice name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/></pq:multichoice>')
    tags = multichoice(element, {'did': 1}, None)
    eq_('<section class="question multichoice"><hgroup><h1>Please choose</h1></hgroup><ul><li><input type="checkbox" name="items.1.choose" value="1" id="items.1.choose-0" /><label for="items.1.choose-0">First</label></li><li><input type="checkbox" name="items.1.choose" value="2" id="items.1.choose-1" /><label for="items.1.choose-1">Middle</label></li><li><input type="checkbox" name="items.1.choose" value="3" id="items.1.choose-2" /><label for="items.1.choose-2">Last</label></li></ul></section>',
        tags.generate().render('xhtml'))

def multichoice_group_test():
    """Tests that the multichoice_gorup element is generated correctly."""
    element = fromstring('<pq:multichoice_group name="choose" title="Please choose" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="1" title="First"/><pq:option value="2" title="Middle"/><pq:option value="3" title="Last"/><pq:multichoice name="q1" title="Question 1"/><pq:multichoice name="q2" title="Question 2"/></pq:multichoice_group>')
    tags = multichoice_group(element, {'did': 1}, None)
    eq_('<section class="question multichoice_group"><hgroup><h1>Please choose</h1></hgroup><table><thead><tr><th></th><th>First</th><th>Middle</th><th>Last</th></tr></thead><tbody><tr><th>Question 1</th><td><input type="checkbox" name="items.1.choose.q1" value="1" /></td><td><input type="checkbox" name="items.1.choose.q1" value="2" /></td><td><input type="checkbox" name="items.1.choose.q1" value="3" /></td></tr><tr><th>Question 2</th><td><input type="checkbox" name="items.1.choose.q2" value="1" /></td><td><input type="checkbox" name="items.1.choose.q2" value="2" /></td><td><input type="checkbox" name="items.1.choose.q2" value="3" /></td></tr></tbody></table></section>',
        tags.generate().render('xhtml'))

def confirm_test():
    """Tests that the confirmation element is generated corrrectly."""
    element = fromstring('<pq:confirm name="confirmation" title="Please confirm this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = confirm(element, {'did': 1}, None)
    eq_('<section class="question confirm"><hgroup><h1>Please confirm this</h1></hgroup><p><input type="checkbox" name="items.1.confirmation" value="true" id="items.1.confirmation" /><label for="items.1.confirmation">Please confirm this</label></p></section>',
        tags.generate().render('xhtml'))
    element = fromstring('<pq:confirm name="confirmation" title="Please confirm this" label="I confirm this" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = confirm(element, {'did': 1}, None)
    eq_('<section class="question confirm"><hgroup><h1>Please confirm this</h1></hgroup><p><input type="checkbox" name="items.1.confirmation" value="true" id="items.1.confirmation" /><label for="items.1.confirmation">I confirm this</label></p></section>',
        tags.generate().render('xhtml'))
    element = fromstring('<pq:confirm name="confirmation" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"/>')
    tags = confirm(element, {'did': 1}, None)
    eq_('<section class="question confirm"><p><input type="checkbox" name="items.1.confirmation" value="true" id="items.1.confirmation" /></p></section>',
        tags.generate().render('xhtml'))

def ranking_test():
    """Tests that the ranking element is generated correctly."""
    element = fromstring('<pq:ranking name="importance" title="Please rank the following items" xmlns:pq="http://paths.sheffield.ac.uk/pyquest"><pq:option value="cat" title="Cat"/><pq:option value="dog" title="Dog"/><pq:option value="mouse" title="Mouse"/></pq:ranking>')
    tags = ranking(element, {'did': 1}, None)
    eq_('<section class="question ranking"><hgroup><h1>Please rank the following items</h1></hgroup><ul><li id="items.1.importance_cat"><select name="items.1.importance.cat" id="items.1.importance.cat"><option value="">--</option><option value="0">1</option><option value="1">2</option><option value="2">3</option></select><label for="items.1.importance.cat">Cat</label></li><li id="items.1.importance_dog"><select name="items.1.importance.dog" id="items.1.importance.dog"><option value="">--</option><option value="0">1</option><option value="1">2</option><option value="2">3</option></select><label for="items.1.importance.dog">Dog</label></li><li id="items.1.importance_mouse"><select name="items.1.importance.mouse" id="items.1.importance.mouse"><option value="">--</option><option value="0">1</option><option value="1">2</option><option value="2">3</option></select><label for="items.1.importance.mouse">Mouse</label></li></ul></section>',
        tags.generate().render('xhtml'))
    