# -*- coding: utf-8 -*-
'''
Created on 20 Jan 2012

@author: mhall
'''
from random import shuffle

from decorator import decorator
from genshi.builder import tag, Markup
from pywebtools import form
from re import search

def get_attr_groups(question, key):
    return [attr_group for attr_group in question.attributes if attr_group.key==key]

def get_qs_attr(qsheet, key, default=None):
    for attr in qsheet.attributes:
        if attr.key == key:
            return attr
    return default

def get_qs_attr_value(qsheet, key, default=None):
    attr = get_qs_attr(qsheet, key, None)
    if attr:
        if attr.value:
            return attr.value
        else:
            return default
    else:
        return default
    
def get_qg_attr(attr_group, key, default=None):
    for attr in attr_group.attributes:
        if attr.key == key:
            return attr
    return default

def get_qg_attr_value(attr_group, key, default=None):
    attr = get_qg_attr(attr_group, key, None)
    if attr:
        if attr.value:
            return attr.value
        else:
            return default
    else:
        return default
    
def get_q_attr(question, key, default=None):
    keys = key.split('.')
    if len(keys) < 2:
        return default
    for attr_group in question.attributes:
        if attr_group.key == keys[0]:
            return get_qg_attr(attr_group, keys[1], default)
    return default
    
def get_q_attr_value(question, key, default=None):
    attr = get_q_attr(question, key, None)
    if attr:
        if attr.value:
            return attr.value
        else:
            return default
    else:
        return default

def question_type_title(q_type):
    if q_type == 'text':
        return 'Static text'
    elif q_type == 'short_text':
        return 'Single-line text input'
    elif q_type == 'long_text':
        return 'Multi-line text input'
    elif q_type == 'number':
        return 'Number input'
    elif q_type == 'email':
        return 'E-Mail input'
    elif q_type == 'url':
        return 'URL input'
    elif q_type == 'date':
        return 'Date input'
    elif q_type == 'time':
        return 'Time input'
    elif q_type == 'datetime':
        return 'Date & Time input'
    elif q_type == 'month':
        return 'Month input'
    elif q_type == 'single_choice':
        return 'Single choice'
    elif q_type == 'multi_choice':
        return 'Multiple choice'
    elif q_type == 'single_choice_grid':
        return 'Single choice grid'
    elif q_type == 'confirm':
        return 'Confirmation checkbox'
    elif q_type == 'multi_choice_grid':
        return 'Multiple choice grid'
    elif q_type == 'ranking':
        return 'Ranking'
    elif q_type == 'auto_commit':
        return 'Automatic next page'
    elif q_type == 'hidden_value':
        return 'Hidden value'
    elif q_type == 'js_check':
        return 'JavaScript check'
    else:
        return q_type
    
def substitute(text, item, participant=None):
    if text:
        m = search('\${.+?}', text)
        while(m):
            tag = m.group(0)[2:-1]
            if participant and tag == 'pid_':
                text = text.replace(m.group(0), unicode(participant.id))
            elif tag in item:
                text = text.replace(m.group(0), unicode(item[tag]))
            else:
                text = text.replace(m.group(0), tag)
            m = search('\${.+?}', text)
        return text
    else:
        return None

def display(question, item, e, csrf_token=None, participant=None):
    if question.type == 'text':
        return tag.section(Markup(substitute(get_q_attr_value(question, 'text.text'), item, participant=participant)))
    elif question.type == 'short_text':
        return short_text_input(question, item, e)
    elif question.type == 'long_text':
        return long_text_input(question, item, e)
    elif question.type == 'number':
        return number_input(question, item, e)
    elif question.type == 'email':
        return email_input(question, item, e)
    elif question.type == 'url':
        return url_input(question, item, e)
    elif question.type == 'date':
        return date_input(question, item, e)
    elif question.type == 'time':
        return time_input(question, item, e)
    elif question.type == 'datetime':
        return datetime_input(question, item, e)
    elif question.type == 'month':
        return month_input(question, item, e)
    elif question.type == 'single_choice':
        subtype = get_q_attr_value(question, 'further.subtype', 'table')
        if subtype == 'table':
            return choice_table(question, item, e)
        elif subtype == 'list':
            return choice_list(question, item, e)
        elif subtype == 'select':
            return choice_select(question, item, e)
    elif question.type == 'multi_choice':
        subtype = get_q_attr_value(question, 'further.subtype', 'table')
        if subtype == 'table':
            return choice_table(question, item, e, multiple=True)
        elif subtype == 'list':
            return choice_list(question, item, e, multiple=True)
        elif subtype == 'select':
            return choice_select(question, item, e, multiple=True)
    elif question.type == 'single_choice_grid':
        return choice_grid(question, item, e)
    elif question.type == 'multi_choice_grid':
        return choice_grid(question, item, e, multiple=True)
    elif question.type == 'confirm':
        return confirm(question, item, e)
    elif question.type == 'ranking':
        return ranking(question, item, e)
    elif question.type == 'auto_commit':
        return auto_commit(question, item, e)
    elif question.type == 'hidden_value':
        return hidden_value(question, item, e)
    elif question.type == 'js_check':
        return js_check(question, item, e)
    else:
        return question.type

def question():
    def wrapper(f, question, item, e, *args, **kwargs):
        tags = f(question, item, e, *args, **kwargs)
        if not isinstance(tags, list):
            tags = [tags]
        if question.title:
            tags.insert(0, tag.hgroup(tag.h1(substitute(question.title, item))))
        return tag.section(tags, class_='question %s' % (question.type))
    return decorator(wrapper)

@question()
def short_text_input(question, item, e):
    return tag.p(form.text_field('items.%s.%s' % (item['did'], question.name), '', e))

@question()
def long_text_input(question, item, e):
    return tag.p(form.textarea('items.%s.%s' % (item['did'], question.name), '', e))

@question()    
def number_input(question, item, e):
    attr = {}
    min_value = get_q_attr_value(question, 'further.min')
    if min_value and min_value.strip() != '':
        attr['min'] = substitute(get_q_attr_value(question, 'further.min'), item)
    max_value = get_q_attr_value(question, 'further.max')
    if max_value and max_value.strip() != '':
        attr['max'] = substitute(get_q_attr_value(question, 'further.min'), item)
    return tag.p(form.number_field('items.%s.%s' % (item['did'], question.name), '', e, **attr))

@question()
def email_input(question, item, e):
    return tag.p(form.email_field('items.%s.%s' % (item['did'], question.name), '', e))
    
@question()
def url_input(question, item, e):
    return tag.p(form.url_field('items.%s.%s' % (item['did'], question.name), '', e))

@question()
def date_input(question, item, e):
    return tag.p(form.date_field('items.%s.%s' % (item['did'], question.name), '' , e))

@question()
def time_input(question, item, e):
    return tag.p(form.time_field('items.%s.%s' % (item['did'], question.name), '' , e))

@question()
def datetime_input(question, item, e):
    return tag.p(form.datetime_field('items.%s.%s' % (item['did'], question.name), '' , e))
        
@question()
def month_input(question, item, e):
    return tag.p(form.month_field('items.%s.%s' % (item['did'], question.name), '' , e))

@question()
def choice_table(question, item, e, multiple=False):
    if multiple:
        render_type = 'checkbox'
    else:
        render_type = 'radio'
    rows = []
    answers = get_attr_groups(question, 'answer')
    headers = map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers)
    values = map(lambda a: tag.td(tag.input(type=render_type,
                                            name='items.%s.%s.answer' % (item['did'], question.name),
                                            value=get_qg_attr_value(a, 'value'))),
                 answers)
    if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
        headers.append(tag.th('Other'))
        values.append(tag.td(tag.input(type=render_type,
                                       name='items.%s.%s.answer' % (item['did'], question.name),
                                       value='_other'),
                             tag.input(type='text',
                                       name='items.%s.%s.other' % (item['did'], question.name),
                                       class_='role-other-text')))
    if get_q_attr_value(question, 'further.before_label'):
        headers.insert(0, tag.th())
        values.insert(0, tag.th(get_q_attr_value(question, 'further.before_label')))
    if get_q_attr_value(question, 'further.after_label'):
        headers.append(tag.th())
        values.append(tag.th(get_q_attr_value(question, 'further.after_label')))
    rows.append(tag.thead(tag.tr(headers)))
    rows.append(tag.tbody(tag.tr(values)))
    return form.error_wrapper(tag.table(rows), 'items.%s.%s' % (item['did'], question.name), e)

@question()
def choice_list(question, item, e, multiple=False):
    if multiple:
        render_type = 'checkbox'
    else:
        render_type = 'radio'
    items = []
    answers = get_attr_groups(question, 'answer')
    for idx, answer in enumerate(answers):
        parts = [tag.input(type=render_type,
                           id='items.%s.%s-%i' % (item['did'], question.name, idx),
                           name='items.%s.%s.answer' % (item['did'], question.name),
                           value=get_qg_attr_value(answer, 'value')),
                 tag.label(get_qg_attr_value(answer, 'label', ''),
                           for_='items.%s.%s-%i' % (item['did'], question.name, idx))]
        items.append(tag.li(parts))
    if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
        items.append(tag.li(tag.input(type=render_type,
                                      name='items.%s.%s.answer' % (item['did'], question.name),
                                      value='_other'
                                      ),
                            tag.input(type='text',
                                      name='items.%s.%s.other' % (item['did'], question.name),
                                      class_='role-other-text')))
    if get_q_attr_value(question, 'further.before_label'):
        items.insert(0, tag.li(get_q_attr_value(question, 'further.before_label')))
    if get_q_attr_value(question, 'further.after_label'):
        items.append(tag.li(get_q_attr_value(question, 'further.after_label')))
    return form.error_wrapper(tag.ul(items), 'items.%s.%s' % (item['did'], question.name), e)

@question()
def choice_select(question, item, e, multiple=False):
    answers = get_attr_groups(question, 'answer')
    items = [tag.option(get_qg_attr_value(answer, 'label'), value=get_qg_attr_value(answer, 'value')) for answer in answers]
    class_ = ''
    if not multiple:
        items.insert(0, tag.option('--- Please choose ---', value=''))
    if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
        items.append(tag.option('--- Other ---', value='_other'))
        class_ = 'role-with-other'
    if multiple:
        para = tag.p(tag.select(items, name='items.%s.%s.answer' % (item['did'], question.name), multiple='multiple', class_=class_))
    else:
        para = tag.p(tag.select(items, name='items.%s.%s.answer' % (item['did'], question.name), class_=class_))
    if get_q_attr_value(question, 'further.allow_other', 'no') == 'single':
        if multiple:
            para.append(tag.br)
        para.append(tag.input(type='text', name='items.%s.%s.other' % (item['did'], question.name),
                              class_='role-other-text'))
    return form.error_wrapper(para,
                              'items.%s.%s' % (item['did'], question.name),
                              e)

@question()
def choice_grid(question, item, e, multiple=False):
    if multiple:
        render_type = 'checkbox'
    else:
        render_type = 'radio'
    answers = get_attr_groups(question, 'answer')
    rows = []
    field_names = ['items.%s.%s' % (item['did'], question.name)]
    for sub_question in get_attr_groups(question, 'subquestion'):
        items = map(lambda a: tag.td(tag.input(type=render_type,
                                               name='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')),
                                               value=get_qg_attr_value(a, 'value'))),
                    answers)
        if get_q_attr_value(question, 'further.before_label'):
            items.insert(0, tag.th(get_q_attr_value(question, 'further.before_label')))
        if get_q_attr_value(question, 'further.after_label'):
            items.append(tag.th(get_q_attr_value(question, 'further.after_label')))
        items.insert(0, tag.th(get_qg_attr_value(sub_question, 'label')))
        rows.append(tag.tr(items))
        field_names.append('items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')))
    headers = map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers)
    if get_q_attr_value(question, 'further.before_label'):
        headers.insert(0, tag.th())
    if get_q_attr_value(question, 'further.after_label'):
        headers.append(tag.th())
    headers.insert(0, tag.th())
    return form.error_wrapper(tag.table(tag.thead(tag.tr(headers)),
                                        tag.tbody(rows)),
                              field_names, e)

@question()
def confirm(question, item, e):
    tags = []
    tags.append(tag.input(type='checkbox',
                          id='items.%s.%s' % (item['did'], question.name),
                          name='items.%s.%s' % (item['did'], question.name),
                          value=get_q_attr_value(question, 'further.value')))
    if get_q_attr_value(question, 'further.label').strip() != '':
        tags.append(tag.label(get_q_attr_value(question, 'further.label'),
                              for_='items.%s.%s' % (item['did'], question.name)))
    elif question.title.strip() != '':
        tags.append(tag.label(question.title,
                              for_='items.%s.%s' % (item['did'], question.name)))
    return form.error_wrapper(tag.p(tags), 'items.%s.%s' % (item['did'], question.name), e)
    
@question()
def multi_choice_grid(question, item, e):
    answers = get_attr_groups(question, 'answer')
    rows = []
    field_names = ['items.%s.%s' % (item['did'], question.name)]
    for sub_question in get_attr_groups(question, 'subquestion'):
        rows.append(tag.tr(tag.th(get_qg_attr_value(sub_question, 'label')),
                           map(lambda a: tag.td(tag.input(type='checkbox',
                                                          name='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')),
                                                          value=get_qg_attr_value(a, 'value'))),
                               answers)))
        field_names.append('items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(sub_question, 'name')))
    return form.error_wrapper(tag.table(tag.thead(tag.tr(tag.th(), map(lambda a: tag.th(get_qg_attr_value(a, 'label')), answers))),
                                        tag.tbody(rows)),
                              field_names, e)

@question()
def ranking(question, item, e):
    answers = get_attr_groups(question, 'answer')
    items = []
    for answer in answers:
        options = [tag.option(idx2 + 1, value=idx2) for idx2 in xrange(0, len(answers))]
        if get_q_attr_value(question, 'further.before_label'):
            options.insert(0, tag.option('-- %s --' % (get_q_attr_value(question, 'further.before_label'))))
        else:
            options.insert(0, tag.option('--', value=''))
        if get_q_attr_value(question, 'further.after_label'):
            options.append(tag.option('-- %s --' % (get_q_attr_value(question, 'further.after_label'))))
        items.append(tag.li(tag.select(options,
                                       id='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(answer, 'value')),
                                       name='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(answer, 'value'))),
                            tag.label(get_qg_attr_value(answer, 'label'), for_='items.%s.%s.%s' % (item['did'], question.name, get_qg_attr_value(answer, 'value'))),
                            id='items.%s.%s.%s-item' % (item['did'], question.name, get_qg_attr_value(answer, 'value'))))
    shuffle(items)
    if get_q_attr_value(question, 'further.before_label'):
        items.insert(0, tag.li(get_q_attr_value(question, 'further.before_label'), class_='role-label', style="display:none;"))
    if get_q_attr_value(question, 'further.after_label'):
        items.append(tag.li(get_q_attr_value(question, 'further.after_label'), class_='role-label', style="display:none;"))
    return form.error_wrapper(tag.ul(items), 'items.%s.%s' % (item['did'], question.name), e)

def auto_commit(question, item, e):
    return Markup('''<script type="text/javascript">$(document).ready(function() {setTimeout(function() {var frm = $('form.role-survey-form'); frm.append('<input type="hidden" name="action_" value="Next Page"/>'); frm.submit();}, %i)});</script>''' % (int(get_q_attr_value(question, 'further.timeout')) * 1000))

def hidden_value(question, item, e):
    return form.hidden_field('items.%s.%s' % (item['did'], question.name), substitute(get_q_attr_value(question, 'further.value', ''), item))

def js_check(q, item, e):
    @question()
    def js_warning(q, item, e):
        if q.required:
            return tag.p('JavaScript is required for this questionnaire')
        else:
            return tag.p('JavaScript is preferred for this questionnaire')
    return tag(tag.noscript(form.error_wrapper(js_warning(q, item, e), 'items.%s.%s' % (item['did'], q.name), e)),
               tag.script(Markup("document.write('%s');" % (Markup(form.hidden_field('items.%s.%s' % (item['did'], q.name), 'yes')))),
                          type_='text/javascript'))

def as_text(qsheet, as_markup=False, no_ids=False):
    def std_attr(question, no_id=False):
        if no_id:
            return 'name="%s" title="%s" help="%s" required="%s"' % (question.name, question.title, question.help, 'true' if question.required else 'false')
        else:
            return 'id="%i" name="%s" title="%s" help="%s" required="%s"' % (question.id, question.name, question.title, question.help, 'true' if question.required else 'false')
    def to_text(question, no_id):
        if question.type == 'text':
            if no_id:
                return '<pq:static_text>%s</pq:static_text>' % (get_q_attr_value(question, 'text.text'))
            else:
                return '<pq:static_text id="%i">%s</pq:static_text>' % (question.id, get_q_attr_value(question, 'text.text'))
        elif question.type == 'short_text':
            return '<pq:short_text %s/>' % (std_attr(question, no_id))
        elif question.type == 'long_text':
            return '<pq:long_text %s/>' % (std_attr(question, no_id))
        elif question.type == 'number':
            return '<pq:number %s min="%s" max="%s"/>' % (std_attr(question, no_id), get_q_attr_value(question, 'further.min', ''), get_q_attr_value(question, 'further.max', ''))
        elif question.type == 'email':
            return '<pq:email %s/>' % (std_attr(question, no_id))
        elif question.type == 'url':
            return '<pq:url %s/>' % (std_attr(question, no_id))
        elif question.type == 'date':
            return '<pq:date %s/>' % (std_attr(question, no_id))
        elif question.type == 'time':
            return '<pq:time %s/>' % (std_attr(question, no_id))
        elif question.type == 'datetime':
            return '<pq:datetime %s/>' % (std_attr(question, no_id))
        elif question.type == 'month':
            return '<pq:month %s/>' % (std_attr(question, no_id))
        elif question.type == 'single_choice':
            lines = ['<pq:single_choice %s display="%s" allow_other="%s" before_label="%s" after_label="%s">' % (std_attr(question, no_id),
                                                                                                                 get_q_attr_value(question, 'further.subtype', 'table'),
                                                                                                                 get_q_attr_value(question, 'further.allow_other', 'no'),
                                                                                                                 get_q_attr_value(question, 'further.before_label', ''),
                                                                                                                 get_q_attr_value(question, 'further.after_label', ''))]
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label', '')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:single_choice>')
            return u'\n'.join(lines) 
        elif question.type == 'multi_choice':
            lines = ['<pq:multi_choice %s display="%s" allow_other="%s" before_label="%s" after_label="%s">' % (std_attr(question, no_id),
                                                                                                                get_q_attr_value(question, 'further.subtype', 'table'),
                                                                                                                get_q_attr_value(question, 'further.allow_other', 'no'),
                                                                                                                get_q_attr_value(question, 'further.before_label', ''),
                                                                                                                get_q_attr_value(question, 'further.after_label', ''))]
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label', '')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:multi_choice>')
            return u'\n'.join(lines) 
        elif question.type == 'single_choice_grid':
            lines = ['<pq:single_choice_grid %s before_label="%s" after_label="%s">' % (std_attr(question, no_id),
                                                                                        get_q_attr_value(question, 'further.before_label', ''),
                                                                                        get_q_attr_value(question, 'further.after_label', ''))]
            lines.extend(['  <pq:sub_question name="%s" label="%s"/>' % (get_qg_attr_value(qg, 'name'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'subquestion')])
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:single_choice_grid>')
            return u'\n'.join(lines)
        elif question.type == 'confirm':
            return '<pq:confirm %s value="%s" label="%s"/>' % (std_attr(question, no_id), get_q_attr_value(question, 'further.value', ''), get_q_attr_value(question, 'further.label', ''))
        elif question.type == 'multi_choice_grid':
            lines = ['<pq:multi_choice_grid %s before_label="%s" after_label="%s">' % (std_attr(question, no_id),
                                                                                       get_q_attr_value(question, 'further.before_label', ''),
                                                                                       get_q_attr_value(question, 'further.after_label', ''))]
            lines.extend(['  <pq:sub_question name="%s" label="%s"/>' % (get_qg_attr_value(qg, 'name'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'subquestion')])
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:multi_choice_grid>')
            return u'\n'.join(lines)
        elif question.type == 'ranking':
            lines = ['<pq:ranking %s before_label="%s" after_label="%s">' % (std_attr(question, no_id),
                                                                             get_q_attr_value(question, 'further.before_label', ''),
                                                                             get_q_attr_value(question, 'further.after_label', ''))]
            lines.extend(['  <pq:answer value="%s" label="%s"/>' % (get_qg_attr_value(qg, 'value'), get_qg_attr_value(qg, 'label')) for qg in get_attr_groups(question, 'answer')])
            lines.append('</pq:ranking>')
            return u'\n'.join(lines)
        elif question.type == 'auto_commit':
            return '<pq:auto_commit timeout="%s"/>' % (get_q_attr_value(question, 'further.timeout', '60')) 
        elif question.type == 'hidden_value':
            return '<pq:hidden_value name="%s" value="%s"/>' % (question.name,
                                                                get_q_attr_value(question, 'further.value', '')) 
        elif question.type == 'js_check':
            return '<pq:js_check %s/>' % (std_attr(question, no_id))
        else:
            return ''
    
    if as_markup:
        return Markup('\n'.join([to_text(q, no_ids) for q in qsheet.questions]))
    else:
        return '\n'.join([to_text(q, no_ids) for q in qsheet.questions])
