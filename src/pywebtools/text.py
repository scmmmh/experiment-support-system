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

def nice_float(value, decimal_places=2):
    fmt_str = '%%.%if' % (decimal_places)
    return fmt_str % (value)
