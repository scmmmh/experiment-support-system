# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
#from pywebtools.auth import is_authorised

from pyramid.httpexceptions import HTTPForbidden

def check_csrf_token(request, params, token_name='csrf_token'):
    if token_name not in params or params[token_name] != request.session.get_csrf_token():
        raise HTTPForbidden('Cross-site request forgery detected')