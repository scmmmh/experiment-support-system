# -*- coding: utf-8 -*-
'''
Created on 14 Feb 2012

@author: mhall
'''

def status(stat):
    if stat == 'develop':
        return 'In Development'
    elif stat == 'testing':
        return 'Testing'
    elif stat == 'running':
        return 'Running'
    elif stat == 'paused':
        return 'Paused'
    elif stat == 'finished':
        return 'Finished'
    else:
        return 'Unknown'
