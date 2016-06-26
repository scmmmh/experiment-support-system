# -*- coding: utf-8 -*-
"""
#################################################################
:mod:`pywebtools.formencode` -- Utilities for use with Formencode
#################################################################

This module provides a number of :class:`~formencode.Schema` and
:class:`~formencode.FancyValidator`.

Of particular note is the :class:`~pywebtools.formencode.CSRFSchema`
which can be used as a base-class instead of :class:`~formencode.Schema`
to automatically include CSRF validation.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from datetime import datetime
from formencode import Schema, FancyValidator, Invalid


class State(object):
    """The :class:`~pywebtools.formencode.State` provides a blank state object for use
    with Formencode validation. Any parameters passed to the constructor are
    automatically set as attributes of the :class:`~pywebtools.State`.
    """

    def __init__(self, **kwargs):
        """Any parameters passed to the constructor are automatically set as
        attributes of the :class:`~pywebtools.State`.
        """
        self.__dict__.update(kwargs)


class CSRFValidator(FancyValidator):
    """Validator that checks a value against the Cross-Site Request Forgery
    token stored in the user's session."""

    messages = {'invalid_csrf_token': 'The CSRF token is invalid. This might indicate a malicious attack.',
                'missing': 'No CSRF token was provided. This might indicate a malicious attack.',
                'empty': 'An empty CSRF token was provided. This might indicate a malicious attack.',
                'no_request': 'No request was specified to validate the CSRFToken'}

    def _validate_python(self, value, state):
        """If a :class:`~pyramid.request.Request` is set in the ``state``, then
        checks whether the ``value`` matches the CSRF token stored in the request.
        """
        if hasattr(state, 'request'):
            if state.request.session.get_csrf_token() != value:
                raise Invalid(self.message('invalid_csrf_token', state), value, state)
        else:
            raise Invalid(self.message('no_request', state), value, state)


class CSRFSchema(Schema):
    """The class:`~pywebtools.formencode.CSRFSchema` is a base :class:`formencode.Schema`
    that includes Cross-Site Request Forgery detection.

    It should be used as the base class for all specific request schemas.
    """

    csrf_token = CSRFValidator(strip=True, not_empty=True)


class UniqueEmailValidator(FancyValidator):
    """The :class:`~pywebtools.formencode.UniqueEmailValidator` checks that the given
    e-mail address is not already used.

    Requires a SQLAlchemy database session to be available via
    ``state.dbsession`` and the user class to be available via ``state.user_class``.
    If a ``state.userid`` is provided, then the ``user_class`` with that ``id`` can
    have the same e-mail address.
    """
    messages = {'existing': 'A user with this e-mail address already exists'}

    def _validate_python(self, value, state):
        if hasattr(state, 'user_class'):
            user = state.dbsession.query(state.user_class).filter(state.user_class.email == value).first()
            if user and (not hasattr(state, 'userid') or user.id != state.userid):
                raise Invalid(self.message('existing', state), value, state)


class EmailDomainValidator(FancyValidator):
    """The :class:`~pywebtools.formencode.EmailDomainValidator` checks that the given
    e-mail address is in the list of allowed e-mail address domains.

    Requires that the list of allowed domains is available via the ``state.email_domains``
    attribute. If nothing is provided in the ``state``, then all e-mail addresses
    are seen as valid.
    """
    messages = {'wrongdomain': 'Only e-mail address in the following domains can be used: %(domains)s'}

    def _validate_python(self, value, state=None):
        if hasattr(state, 'email_domains') and state.email_domains:
            value = value[value.find('@') + 1:]
            if isinstance(state.email_domains, list):
                if value not in state.email_domains:
                    raise Invalid(self.message('wrongdomain',
                                               state,
                                               domains=', '.join(state.email_domains)),
                                  value,
                                  state)
            elif value != state.email_domains:
                raise Invalid(self.message('wrongdomain',
                                           state,
                                           domains=state.email_domains),
                              value,
                              state)


class PasswordValidator(FancyValidator):
    """The :class:`~pywebtools.formencode.PasswordValidator` handles the checking of
    user-provided passwords against the database to allow / dissallow login.

    Requires a SQLAlchemy database session to be available via ``state.dbsession``.
    """

    messages = {'nologin': 'No user exists with the given e-mail address or the password does not match'}

    def _validate_python(self, value, state):
        if hasattr(state, 'user_class'):
            user = state.dbsession.query(state.user_class).\
                filter(state.user_class.email == value['email'].lower()).first()
            if user:
                if not user.password_matches(value['password']):
                    raise Invalid(self.message('nologin', state), value, state)
            else:
                raise Invalid(self.message('nologin', state), value, state)
        else:
            raise Invalid(self.message('nologin', state), value, state)


class DynamicSchema(Schema):
    """The :class:`~pywebtools.formencode.DynamicSchema` provides a dynamic
    :class:`~schema.Schema` for which the validation fields are defined from
    the ``list`` of (field-name, :class:`~FancyValidator`) pairs passed to the
    constructor.
    """
    accept_iterator = True

    def __init__(self, fields=None, **kwargs):
        Schema.__init__(self, **kwargs)
        if fields:
            for (name, validator) in fields:
                self.add_field(name, validator)


class DateValidator(FancyValidator):
    """The :class:`~pywebtools.formencode.DateValidator` provides date validation and
    conversion from the formats "YYYY-MM-DD" or "DD/MM/YYYY" to a python
    :class:`datetime.date`.
    """

    messages = {'invalid_format': 'Please enter a date either as YYYY-MM-DD or DD/MM/YYYY'}

    def _convert_to_python(self, value, state):
        """Try to convert from either "YYYY-MM-DD" or "DD-MM-YYYY" to a
        :class:`datetime.date`. Raises :class:`~Invalid` if the
        conversion fails.

        :param value: The `unicode` value to convert
        :param type: `unicode`
        :return: The converted date
        :return_type: :class:`datetime.date`.
        """
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except:
            try:
                return datetime.strptime(value, '%d/%m/%Y').date()
            except:
                raise Invalid(self.message('invalid_format', state), value, state)


class TimeValidator(FancyValidator):
    """The :class:`~pywebtools.formencode.DateValidator` provides time validation and
    conversion from the format "HH:MM" to a python :class:`datetime.time`.
    """

    messages = {'invalid_format': 'Please enter a time as HH:MM'}

    def _convert_to_python(self, value, state):
        """Try to convert from "HH:MM" to a :class:`datetime.time`. Raises
        :class:`~Invalid` if the conversion fails.

        :param value: The `unicode` value to convert
        :param type: `unicode`
        :return: The converted time
        :return_type: :class:`datetime.time`
        """
        try:
            return datetime.strptime(value, '%H:%M').time()
        except Exception:
            raise Invalid(self.message('invalid_format', state), value, state)
