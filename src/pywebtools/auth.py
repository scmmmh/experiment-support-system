# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''

class AuthorisationException(Exception):
    
    def __init__(self, message):
        self.message = message
    
    def __repr_(self):
        return 'AuthorisationException(%s)' % repr(self.message)
    
    def __str__(self):
        return self.message

def parse_authentication_string(auth_string, params):
    def obj(src, token):
        while token == ' ':
            token = src()
        if token == ':':
            obj_name = []
            token = src()
            while token not in ['.', ')', ':']:
                obj_name.append(token)
                token = src()
            return ('obj', ''.join(obj_name), atom(src, token))
    def method(src, token):
        if token == '.':
            method_name = []
            token = src()
            while token != '(' and token != ' ':
                method_name.append(token)
                token = src()
            if token == '(':
                return ('mthd', ''.join(method_name), atom(src, token))
            elif token == ' ':
                return ('mthd', ''.join(method_name), [])
    def atom(src, token):
        if token == ':':
            return obj(src, token)
        elif token == '.':
            return method(src, token)
        elif token == '(':
            return []
    src = (c for c in auth_string)
    print atom(src.next, src.next())
    return False
    
def is_authorised(auth_string, **params):
    #ops = parse_authentication_string(auth_string, params)
    return True
