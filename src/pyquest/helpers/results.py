# -*- coding: utf-8 -*-
'''
Created on 8 Feb 2012

@author: mhall
'''

def has_result(qsheet, data_item, question, participants):
    for participant in participants:
        if qsheet in participant and data_item in participant[qsheet]['items'] \
                and question in participant[qsheet]['items'][data_item]:
            return True
    return False

def summary_boolean(qsheet, data_item, question, participants):
    if len(participants) > 0:
        true_count = 0
        false_count = 0
        for participant in participants:
            if qsheet in participant and data_item in participant[qsheet]['items'] \
                    and question in participant[qsheet]['items'][data_item]:
                if participant[qsheet]['items'][data_item][question]:
                    true_count = true_count + 1
                else:
                    false_count = false_count + 1
        return 'Yes: %i; No: %i; Total: %i' % (true_count, false_count, len(participants))
    else:
        return '-'

def summary_single_in_list(qsheet, data_item, question, question_attr, participants):
    if len(participants) > 0:
        counts = {}
        for value in question_attr['values']:
            counts[value] = 0
        for participant in participants:
            if qsheet in participant and data_item in participant[qsheet]['items'] \
                    and question in participant[qsheet]['items'][data_item]:
                value = participant[qsheet]['items'][data_item][question]
                if value in counts:
                    counts[value] = counts[value] + 1
        result = []
        total = reduce(lambda a, b: a + b, counts.values())
        for value in question_attr['values']:
            result.append('%s: %i' % (value, counts[value]))
        result.append('Total: %s' % (total))
        return '; '.join(result)
    else:
        return ''

def question_summary(qsheet, data_item, question, question_attr, participants):
    if question_attr['type'] == 'boolean':
        return summary_boolean(qsheet, data_item, question, participants)
    elif question_attr['type'] == 'single_in_list':
        return summary_single_in_list(qsheet, data_item, question, question_attr, participants)
    elif question_attr['type'] == 'multi_in_list':
        pass
    elif question_attr['type'] == 'number':
        pass
    elif question_attr['type'] == 'unicode':
        pass
    elif question_attr['type'] == 'email':
        pass
    elif question_attr['type'] == 'url':
        pass
    elif question_attr['type'] == 'date':
        pass
    elif question_attr['type'] == 'time':
        pass
    elif question_attr['type'] == 'datetime':
        pass
    elif question_attr['type'] == 'month':
        pass
    elif question_attr['type'] == 'all_in_list':
        pass
    else:
        return '-'