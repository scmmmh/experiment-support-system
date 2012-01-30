# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2012

@author: mhall
'''
def title(string):
    if len(string) > 0:
        return string[0].upper() + string[1:]
    else:
        return string
