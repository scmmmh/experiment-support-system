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

def test_parse():
    eq_([(VAL, True)],
        parse(tokenise('True')))
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

def test_basic_is_authorised():
    eq_(True,
        is_authorised('True', {}))
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
    