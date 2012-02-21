# -*- coding: utf-8 -*-
'''
Created on 15 Feb 2012

@author: mhall
'''
from nose.tools import eq_

from pywebtools.auth import (AuthorisationException, tokenise, parse,
                             infix_to_reverse_polish, is_authorised,
                             IDENT, OP, BRACE_LEFT, BRACE_RIGHT, OBJ, VAL, CALL)

def test_tokenise():
    eq_([(OBJ, 'user')],
        tokenise(':user'))
    eq_([(OBJ, 'user'), (OP, '.'), (IDENT, 'is-logged-in')],
        tokenise(':user.is-logged-in'))
    eq_([(OBJ, 'user'), (OP, '.'), (IDENT, 'is-logged-in'), (OP, 'or'), (OBJ, 'user'), (OP, '.'), (IDENT, 'has-right'), (BRACE_LEFT, '('), (IDENT, 'test'), (BRACE_RIGHT, ')')],
        tokenise(':user.is-logged-in or :user.has-right(test)'))
    eq_([(OBJ, 'user'), (OP, '.'), (IDENT, 'is-logged-in'), (BRACE_LEFT, '('), (BRACE_RIGHT, ')')],
        tokenise(' :user.is-logged-in()'))
    eq_([(OP, '.'), (IDENT, 'is-logged-in'), (BRACE_LEFT, '('), (BRACE_RIGHT, ')')],
        tokenise('.is-logged-in()'))
    eq_([(OBJ, 'user'), (OP, '.'), (IDENT, 'is-logged-in'), (BRACE_LEFT, '('), (BRACE_RIGHT, ')'), (OP, '=='), (IDENT, 'True')],
        tokenise(' :user.is-logged-in() == True'))
    eq_([(OBJ, 'user'), (OP, '.'), (IDENT, 'is-logged-in'), (BRACE_LEFT, '('), (BRACE_RIGHT, ')'), (OP, '!='), (IDENT, 'True')],
        tokenise(' :user.is-logged-in() != True'))
    eq_([(OBJ, 'survey'), (OP, '.'), (IDENT, 'is-owned-by'), (BRACE_LEFT, '('), (OBJ, 'user'), (BRACE_RIGHT, ')')],
        tokenise(':survey.is-owned-by(:user)'))
    eq_([(OBJ, 'user'), (OP, '.'), (IDENT, 'has-right'), (BRACE_LEFT, '('), (VAL, "'test.yes'"), (BRACE_RIGHT, ')')],
        tokenise(":user.has-right('test.yes')"))
    eq_([(OBJ, 'user'), (OP, '.'), (IDENT, 'has-right'), (BRACE_LEFT, '('), (VAL, '"test.yes"'), (BRACE_RIGHT, ')')],
        tokenise(':user.has-right("test.yes")'))

def test_value_parse():
    eq_([(VAL, True)],
        parse(tokenise('True')))
    eq_([(VAL, False)],
        parse(tokenise('False')))
    eq_([(VAL, 4)],
        parse(tokenise('4')))
    eq_([(VAL, 3.4)],
        parse(tokenise('3.4')))
    eq_([(VAL, 'nobody')],
        parse(tokenise('nobody')))
    eq_([(VAL, 'True')],
        parse(tokenise('"True"')))
    eq_([(VAL, '4')],
        parse(tokenise("'4'")))

def test_parse():
    eq_([(OBJ, 'user')],
        parse(tokenise(':user')))
    eq_([(CALL, 'user', 'is-logged-in')],
        parse(tokenise(':user.is-logged-in')))
    eq_([(CALL, 'user', 'is-logged-in')],
        parse(tokenise(':user.is-logged-in()')))
    eq_([(CALL, 'user', 'has-right', (VAL, 'test'))],
        parse(tokenise(':user.has-right(test)')))
    eq_([(CALL, 'user', 'is-logged-in'), (OP, 'or'), (CALL, 'user', 'has-right', (VAL, 'test'))],
        parse(tokenise(':user.is-logged-in or :user.has-right(test)')))
    eq_([(CALL, 'user', 'is-logged-in'), (OP, '=='), (VAL, True)],
        parse(tokenise(':user.is-logged-in() == True')))
    eq_([(CALL, 'user', 'is-logged-in'), (OP, '!='), (VAL, True)],
        parse(tokenise(':user.is-logged-in != True')))
    eq_([(CALL, 'survey', 'is-owned-by', (OBJ, 'user'))],
        parse(tokenise(':survey.is-owned-by(:user)')))
    eq_([(CALL, 'survey', 'is-owned-by', (VAL, ':user'))],
        parse(tokenise(':survey.is-owned-by(":user")')))
    eq_([(CALL, 'survey', 'is-owned-by', (VAL, '4'))],
        parse(tokenise(':survey.is-owned-by("4")')))
    eq_([(CALL, 'survey', 'is-owned-by', (VAL, 3))],
        parse(tokenise(':survey.is-owned-by(3)')))
    eq_([(CALL, 'survey', 'is-owned-by', (VAL, 3.2))],
        parse(tokenise(':survey.is-owned-by(3.2)')))
    eq_([(CALL, 'survey', 'is-owned-by', (VAL, True))],
        parse(tokenise(':survey.is-owned-by(True)')))

def test_infix_to_inverse_polish():
    eq_([(CALL, 'user', 'is-logged-in'), (CALL, 'user', 'has-right', (VAL, 'test')), (OP, 'or')],
        infix_to_reverse_polish(parse(tokenise(':user.is-logged-in or :user.has-right(test)'))))
    eq_([(CALL, 'user', 'is-logged-in'), (VAL, True), (OP, '==')],
        infix_to_reverse_polish(parse(tokenise(':user.is-logged-in() == True'))))
    eq_([(CALL, 'user', 'is-logged-in'), (VAL, True), (OP, '!=')],
        infix_to_reverse_polish(parse(tokenise(':user.is-logged-in != True'))))
    eq_([(CALL, 'user', 'is-logged-in'), (CALL, 'user', 'id'), (CALL, 'user2', 'id'), (OP, '=='), (OP, 'or')],
        infix_to_reverse_polish(parse(tokenise(':user.is-logged-in or :user.id == :user2.id'))))
    eq_([(CALL, 'user', 'is-logged-in'), (CALL, 'user', 'has-right', (VAL, 'test')), (OP, 'or'), (CALL, 'user', 'id'), (CALL, 'user2', 'id'), (OP, '=='), (OP, 'and')],
        infix_to_reverse_polish(parse(tokenise('(:user.is-logged-in or :user.has-right(test)) and :user.id == :user2.id'))))
    eq_([(CALL, 'cuser', 'is-logged-in'), (CALL, 'cuser', 'id'), (CALL, 'user', 'id'), (OP, '=='), (CALL, 'user', 'has-right', (VAL, 'test')), (OP, 'or'), (OP, 'and')],
        infix_to_reverse_polish(parse(tokenise(':cuser.is-logged-in and (:cuser.id == :user.id or :user.has-right(test))'))))
    eq_([(CALL, 'survey', 'is-owned-by', (OBJ, 'user'))],
        infix_to_reverse_polish(parse(tokenise(':survey.is-owned-by(:user)'))))

class TestUser(object):
    
    def __init__(self, val=None, logged_in=False, rights=None):
        self.val = val
        self.logged_in = logged_in
        if rights:
            self.rights = rights
        else:
            self.rights = []
    
    def value(self):
        return self.val
    
    def is_logged_in(self):
        return self.logged_in
    
    def has_right(self, right):
        return right in self.rights

class TestObj(object):
    
    def __init__(self, owned_by=True):
        self.owned_by = owned_by
    
    def is_owned_by(self, user):
        return user and self.owned_by
            
def test_basic_is_authorised():
    eq_(True,
        is_authorised('True', {}))
    eq_(True,
        is_authorised(':user', {'user': TestUser()}))
    eq_(False,
        is_authorised(':user', {}))
    eq_(True,
        is_authorised(':user.is-logged-in', {'user': TestUser(logged_in=True)}))
    eq_(True,
        is_authorised(':user.logged-in', {'user': TestUser(logged_in=True)}))
    eq_(True,
        is_authorised(':user.has-right(test)', {'user': TestUser(rights=['test'])}))
    eq_(True,
        is_authorised(':user.is-logged-in and :user.has-right(test)', {'user': TestUser(logged_in=True, rights=['test'])}))
    eq_(False,
        is_authorised(':user.is-logged-in and :user.has-right(test)', {'user': TestUser(rights=['test'])}))
    eq_(True,
        is_authorised(':user.is-logged-in or :user.has-right(test)', {'user': TestUser(logged_in=True)}))
    eq_(True,
        is_authorised(':user.is-logged-in or :user.has-right(test)', {'user': TestUser(rights=['test'])}))
    eq_(True,
        is_authorised(':user1.value == :user2.value', {'user1': TestUser(val=1), 'user2': TestUser(val=1)}))
    eq_(False,
        is_authorised(':user1.value == :user2.value', {'user1': TestUser(val=1), 'user2': TestUser(val=2)}))
    eq_(True,
        is_authorised(':user1.value != :user2.value', {'user1': TestUser(val=1), 'user2': TestUser(val=2)}))
    eq_(False,
        is_authorised(':user1.value != :user2.value', {'user1': TestUser(val=1), 'user2': TestUser(val=1)}))
    eq_(True,
        is_authorised(':survey.is-owned-by(:user)', {'survey': TestObj(True), 'user': TestUser()}))
    eq_(False,
        is_authorised(':survey.is-owned-by(:user)', {'survey': TestObj(False), 'user': TestUser()}))
    eq_(False,
        is_authorised(':survey.is-owned-by(:user)', {'survey': TestObj(True), 'user': None}))

def test_complex_is_authorised():
    eq_(True,
        is_authorised('(:user1.value == :user2.value and :user1.logged-in) or :user2.logged-in', {'user1': TestUser(val=1, logged_in=True), 'user2': TestUser(val=1)}))
    eq_(True,
        is_authorised('(:user1.value == :user2.value and :user1.logged-in) or :user2.logged-in', {'user1': TestUser(val=1), 'user2': TestUser(logged_in=True, val=2)}))
    eq_(True,
        is_authorised('(:user1.value == :user2.value and :user1.logged-in) or :user2.logged-in', {'user1': TestUser(val=1, logged_in=False), 'user2': TestUser(logged_in=True, val=1)}))
    eq_(False,
        is_authorised('(:user1.value == :user2.value and :user1.logged-in) or :user2.logged-in', {'user1': TestUser(val=1, logged_in=True), 'user2': TestUser(val=2)}))
    eq_(False,
        is_authorised('(:user1.value == :user2.value and :user1.logged-in) or :user2.logged-in', {'user1': TestUser(val=1, logged_in=False), 'user2': TestUser(val=1)}))
    