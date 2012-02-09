# -*- coding: utf-8 -*-
'''
Created on 9 Feb 2012

@author: mhall
'''

from genshi.builder import tag

def menu(items, current, **kwargs):
    menu_items = []
    for item in items:
        if item[0] == current:
            menu_items.append(tag.li(tag.a(item[1], **item[2]), class_='current'))
        else:
            menu_items.append(tag.li(tag.a(item[1], **item[2])))
    return tag.nav(tag.ul(menu_items), **kwargs)
