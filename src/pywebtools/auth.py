# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''

import collections
import re

OBJ = 'OBJ'
VAL = 'VAL'
CALL = 'CALL'
IDENT = 'IDENT'
OP = 'OP'
BRACE_LEFT = 'BRLEFT'
BRACE_RIGHT = 'BRRIGHT'

class AuthorisationException(Exception):
    
    def __init__(self, message):
        self.message = message
    
    def __repr_(self):
        return 'AuthorisationException(%s)' % repr(self.message)
    
    def __str__(self):
        return self.message

def tokenise(auth_string):
    def process(token):
        token = ''.join(token)
        if token == '(':
            return (BRACE_LEFT, token)
        elif token == ')':
            return (BRACE_RIGHT, token)
        elif token.lower() in ['.', '==', '!=', 'or', 'and']:
            return (OP, token.lower())
        elif token.startswith(':'):
            return (OBJ, token[1:])
        else:
            return (IDENT, token)
    tokens = []
    token = []
    string_marker = None
    for char in auth_string:
        if string_marker:
            if char == string_marker:
                token.append(char)
                tokens.append((VAL, ''.join(token)))
                token = []
                string_marker = None
            else:
                token.append(char)
        else:
            if char in ['(', ')', '.']:
                if token:
                    tokens.append(process(token))
                    token = []
                tokens.append(process(char))
            elif char in ['!', '=']:
                if token:
                    if len(token) > 1 or token[0] not in ['!', '=']:
                        tokens.append(process(token))
                        token = []
                token.append(char)
            elif char == ' ':
                if token:
                    tokens.append(process(token))
                    token = []
            elif char in ["'", '"']:
                if token:
                    tokens.append(process(token))
                    token = []
                token.append(char)
                string_marker = char
            else:
                token.append(char)
    if string_marker:
        raise AuthorisationException("Invalid authorisation statement. Unterminated string literal.")
    if token:
        tokens.append(process(token))
    return tokens

def parse(tokens):
    def value(token):
        if token[1] == 'True':
            return (VAL, True)
        elif token[1] == 'False':
            return (VAL, False)
        elif re.match(r'[0-9]+', token[1]):
            return (VAL, int(token[1]))
        elif token[1].startswith("'") and token[1].endswith("'"):
            return (VAL, token[1][1:-1])
        elif token[1].startswith('"') and token[1].endswith('"'):
            return (VAL, token[1][1:-1])
        else:
            return (VAL, token[1])
    def float_value(token, tokens):
        if len(tokens) > 0:
            ntoken = tokens.pop()
            if ntoken[0] == OP and ntoken[1] == '.':
                ntoken2 = tokens.pop()
                if ntoken2[0] == IDENT and isinstance(value(ntoken2)[1], int):
                    return (VAL, float('%s.%s' % (token[1], ntoken2[1])))
                else:
                    tokens.append(ntoken2)
                    tokens.append(ntoken)
                    return token
            else:
                tokens.append(ntoken)
                return token
        else:
            return token
    def params(tokens):
        param_list = []
        while True:
            if len(tokens) == 0:
                raise AuthorisationException('Invalid authorisation statement: Was expecting IDENT, OBJ, VAL, or ), but got EOL')
            ntoken = tokens.pop()
            if ntoken[0] == IDENT:
                tmp = value(ntoken)
                if tmp[0] == VAL and isinstance(tmp[1], int):
                    param_list.append(float_value(tmp, tokens))
                else:
                    param_list.append(tmp)
            elif ntoken[0] == OBJ:
                param_list.append(ntoken)
            elif ntoken[0] == VAL:
                param_list.append(value(ntoken))
            elif ntoken[0] == BRACE_RIGHT:
                break
            else:
                raise AuthorisationException('Invalid authorisation statement: Was expecting IDENT, OBJ, VAL, or ), but got %s' % (ntoken[1]))
        return param_list
    def obj(token, tokens):
        if len(tokens) == 0:
            return (OBJ, token[1])
        ntoken = tokens.pop()
        if ntoken == (OP, '.'):
            if len(tokens) == 0:
                raise AuthorisationException('Invalid authorisation statement: Was expecting IDENT, but got EOL')
            ntoken = tokens.pop()
            if ntoken[0] == IDENT:
                result = [CALL, token[1], ntoken[1]]
                if len(tokens) > 0:
                    ntoken = tokens.pop()
                    if ntoken[0] == BRACE_LEFT:
                        result.extend(params(tokens))
                    else:
                        tokens.append(ntoken)
                return tuple(result)
    output = []
    tokens.reverse()
    while len(tokens) > 0:
        ntoken = tokens.pop()
        if ntoken[0] == OBJ:
            output.append(obj(ntoken, tokens))
        elif ntoken[0] == IDENT:
            tmp = value(ntoken)
            if tmp[0] == VAL and isinstance(tmp[1], int):
                output.append(float_value(tmp, tokens))
            else:
                output.append(tmp)
        elif ntoken[0] == VAL:
            output.append(value(ntoken))
        elif ntoken[0] == OP and ntoken[1] == '.':
            raise AuthorisationException('Invalid authorisation statement. Was expecting one of OBJ, IDENT, VAL, OP, or BRACE_LEFT, but got .')
        else:
            output.append(ntoken)
    return output

def infix_to_reverse_polish(tokens):
    def op_precedence(token):
        if token[0] == BRACE_LEFT:
            return 0
        elif token[0] == OP and token[1] in ['==', '!=']:
            return 2
        else:
            return 1
    output = []
    stack = []
    for token in tokens:
        if token[0] == BRACE_LEFT:
            stack.append(token)
        elif token[0] == BRACE_RIGHT:
            while True:
                if len(stack) == 0:
                    raise AuthorisationException('Invalid authorisation statement: Too many ).')
                ntoken = stack.pop()
                if ntoken[0] == BRACE_LEFT:
                    break
                else:
                    output.append(ntoken)
        elif token[0] == OP:
            while len(stack) > 0:
                ntoken = stack.pop()
                if op_precedence(token) > op_precedence(ntoken):
                    stack.append(ntoken)
                    break
                else:
                    output.append(ntoken)
            stack.append(token)
        else:
            output.append(token)
    while len(stack) > 0:
        ntoken = stack.pop()
        if ntoken[0] == BRACE_LEFT:
            raise AuthorisationException('Invalid authorisation statement: Missing ).')
        output.append(ntoken)
    return output

def is_authorised(auth_string, objects):
    stack = []
    for token in infix_to_reverse_polish(parse(tokenise(auth_string))):
        if token[0] == VAL:
            stack.append(token)
        elif token[0] == OBJ:
            if token[1] in objects:
                stack.append((OBJ, objects[token[1]]))
            else:
                stack.append((OBJ, None))
        elif token[0] == CALL:
            if token[1] in objects:
                obj = objects[token[1]]
                func = token[2].replace('-', '_')
                if hasattr(obj, func):
                    attr = getattr(obj, func)
                    if isinstance(attr, collections.Callable):
                        params = []
                        for param in token[3:]:
                            if param[0] == OBJ:
                                if param[1] in objects:
                                    params.append(objects[param[1]])
                                else:
                                    params.append(None)
                            elif param[0] == VAL:
                                params.append(param[1])
                            else:
                                raise AuthorisationException('Invalid authorisation statement. Was expecting OBJ or VAL, but got %s' % (param[1]))
                        print params
                        stack.append((VAL, attr(*params)))
                    else:
                        stack.append((VAL, attr))
                else:
                    stack.append((VAL, False))
            else:
                stack.append((VAL, False))
        elif token[0] == OP:
            if len(stack) < 2:
                raise AuthorisationException('Invalid authorisation statement: Too few operands')
            op2 = stack.pop()
            op1 = stack.pop()
            if token[1] == 'and':
                stack.append((VAL, op1[1] and op2[1]))
            elif token[1] == 'or':
                stack.append((VAL, op1[1] or op2[1]))
            elif token[1] == '!=':
                stack.append((VAL, op1[1] != op2[1]))
            elif token[1] == '==':
                stack.append((VAL, op1[1] == op2[1]))
        else:
            raise AuthorisationException('Internal authorisation execution error.')
    if len(stack) == 0:
        raise AuthorisationException('Empty authorisation statement')
    elif len(stack) > 1:
        raise AuthorisationException('Invalid authorisation statement: Missing operator')
    return bool(stack[0][1])
