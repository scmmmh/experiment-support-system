# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: mhall
'''
from pyramid.httpexceptions import HTTPForbidden

def check_csrf_token(request, token):
    if token != request.session.get_csrf_token():
        raise HTTPForbidden('Cross-site request forgery detected')