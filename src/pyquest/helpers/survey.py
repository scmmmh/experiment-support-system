# -*- coding: utf-8 -*-
'''
Created on 14 Feb 2012

@author: mhall
'''

from genshi.builder import tag

def status(stat, lower_case=False):
    if stat == 'develop':
        if lower_case:
            return 'in development'
        else:
            return 'In Development'
    elif stat == 'testing':
        if lower_case:
            return 'testing'
        else:
            return 'Testing'
    elif stat == 'running':
        if lower_case:
            return 'running'
        else:
            return 'Running'
    elif stat == 'paused':
        if lower_case:
            return 'paused'
        else:
            return 'Paused'
    elif stat == 'finished':
        if lower_case:
            return 'finished'
        else:
            return 'Finished'
    else:
        if lower_case:
            return 'unknown'
        else:
            return 'Unknown'

def fancy_status(request, stat, lower_case=False, **kwargs):
    return tag.p(tag.span(status(stat, lower_case)),
                 tag.img(src=request.static_url('pyquest:static/img/%s.png' % stat), alt=status(stat, lower_case)),
                 **kwargs)
