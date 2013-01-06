# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
def convert_type(value, target_type, default=None):
    if target_type == 'int':
        try:
            return int(value)
        except ValueError:
            return default
    return value