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

def fancy_status(request, survey, lower_case=False, **kwargs):
    target_status = []
    if survey.status == 'develop':
        target_status = [tag.li(tag.a('Test', href=request.route_url('survey.status', sid=1, _query={'status': 'testing'}), class_='post-submit', data_confirm='no-confirm')),
                         tag.li(tag.a('Start', href=request.route_url('survey.status', sid=1, _query={'status': 'running'}), class_='post-submit', data_confirm='no-confirm'))]
    elif survey.status == 'testing':
        target_status = [tag.li(tag.a('Stop Test', href=request.route_url('survey.status', sid=1, _query={'status': 'develop'}), class_='post-submit', data_confirm='no-confirm'))]
    elif survey.status == 'running':
        target_status = [tag.li(tag.a('Pause', href=request.route_url('survey.status', sid=1, _query={'status': 'paused'}), class_='post-submit', data_confirm='no-confirm')),
                         tag.li(tag.a('Finish', href=request.route_url('survey.status', sid=1, _query={'status': 'finished'}), class_='post-submit', data_confirm='no-confirm'))]
    elif survey.status in 'paused':
        target_status = [tag.li(tag.a('Restart', href=request.route_url('survey.status', sid=1, _query={'status': 'running'}), class_='post-submit', data_confirm='no-confirm')),
                         tag.li(tag.a('Finish', href=request.route_url('survey.status', sid=1, _query={'status': 'finished'}), class_='post-submit', data_confirm='no-confirm'))]
    elif survey.status in 'finished':
        target_status = [tag.li(tag.a('Restart', href=request.route_url('survey.status', sid=1, _query={'status': 'running'}), class_='post-submit', data_confirm='no-confirm'))]
    return tag.div(tag.p(tag.span(status(survey.status, lower_case)),
                         tag.img(src=request.static_url('pyquest:static/img/%s.png' % survey.status), alt=status(survey.status, lower_case))),
                   tag.ul(target_status, class_='status-changer', style='display:none;'),
                   **kwargs)
