from ess import models
from ess.importexport import (PageIOSchema, QuestionIOSchema, QuestionTypeIOSchema, QuestionTypeGroupIOSchema)

def test_question_type_group_import():
    """Test importing question type structures"""
    schema = QuestionTypeGroupIOSchema()
    loaded,errors = schema.load({'data': {'type': 'question_type_groups',
                                   'id': '2',
                                   'attributes': {'title': 'Core Questions',
                                                  'name': 'ess:core',
                                                  'order': 1,
                                                  'enabled': True},
                                   'relationships': {'parent': {'data': {'type': 'question_type_groups',
                                                                         'id': '1'}}}},
                          'included': [{'type': 'question_type_groups',
                                        'id': '1',
                                        'attributes': {'title': 'Builtin Questions',
                                                       'name': 'ess:builtin',
                                                       'order': 2,
                                                       'enabled': True}}]})
    assert isinstance(loaded, models.QuestionTypeGroup)
    assert loaded.title == 'Core Questions'
    assert loaded.name == 'ess:core'
    assert loaded.order == 1
    assert loaded.enabled == True
    assert loaded.parent.title == 'Builtin Questions'
    assert loaded.parent.name == 'ess:builtin'
    assert loaded.parent.order == 2
    assert loaded.parent.enabled == True
    assert loaded.parent.parent is None


def test_question_type_import():
    """Test importing question types and the groups they belong to."""
    schema = QuestionTypeIOSchema(include_schemas=(QuestionTypeGroupIOSchema,), many=True)
    loaded = schema.load(
                  {'data': [{'type': 'question_types',
                             'id': '1',
                             'attributes': {'name': 'text',
                                            'title': 'Static Text',
                                            'enabled': True,
                                            'order': 0,
                                            'frontend': {'text': '<p>Enter the text to display.</p>'},
                                            'backend': {'fields': []}},
                             'relationships': {'q_type_group': {'data': {'type': 'question_type_groups', 'id': '1'}}}},
                            {'type': 'question_types',
                                     'id': '3',
                                     'attributes': {'name': 'language',
                                                    'title': 'Language Selection',
                                                    'enabled': True,
                                                    'order': 2,
                                                    'frontend': {'text': '<p>Enter the text to display.</p>'},
                                                    'backend': {'fields': []}},
                                     'relationships': {'q_type_group': {'data': {'type': 'question_type_groups', 'id': '1'}},
                                                       'parent': {'data': {'type': 'question_types', 'id': '2'}}}}],
                   'included': [{'type': 'question_type_groups',
                                 'id': '1',
                                 'attributes': {'title': 'Builtin Questions',
                                                'name': 'ess:builtin',
                                                'order': 1,
                                                'enabled': True}},
                                {'type': 'question_types',
                                 'id': '2',
                                 'attributes': {'name': 'select',
                                                'title': 'Simple Selection',
                                                'enabled': True,
                                                'order': 1,
                                                'frontend': {'text': '<p>Enter the text to display.</p>'},
                                                'backend': {'fields': []}},
                                 'relationships': {'q_type_group': {'data': {'type': 'question_type_groups', 'id': '1'}}}}]}).data
    assert isinstance(loaded, list)
    assert len(loaded) == 2
    assert isinstance(loaded[0], models.QuestionType)
    assert loaded[0].name == 'text'
    assert loaded[0].q_type_group is not None
    assert isinstance(loaded[0].q_type_group, models.QuestionTypeGroup)
    assert loaded[0].parent is None
    assert isinstance(loaded[1], models.QuestionType)
    assert loaded[1].name == 'language'
    assert loaded[1].q_type_group is not None
    assert isinstance(loaded[0].q_type_group, models.QuestionTypeGroup)
    assert loaded[1].parent is not None
    assert isinstance(loaded[1].parent, models.QuestionType)


def test_page_import_minimal():
    schema = PageIOSchema(include_schemas=(QuestionTypeIOSchema, QuestionTypeGroupIOSchema, QuestionIOSchema))
    page, errors = schema.load({'data': {'type': 'pages',
                                         'id': '1',
                                         'attributes': {'name': 'test',
                                                        'title': 'Test Page'},
                                         'relationships': {'questions': {'data': []},
                                                           'next': {'data': []},
                                                           'prev': {'data': []},
                                                           'data_set': {'data': None}}}})
    assert errors == {}
    assert page.name == 'test'
    assert page.title == 'Test Page'


def test_page_import_full():
    schema = PageIOSchema(include_schemas=(QuestionTypeIOSchema, QuestionTypeGroupIOSchema, QuestionIOSchema))
    page, errors = schema.load({'data': {'type': 'pages',
                                         'id': '1',
                                         'attributes': {'name': 'test',
                                                        'title': 'Test Page',
                                                        'scripts': 'alert("");',
                                                        'styles': 'body {}',
                                                        'attributes': {'number_questions': True}},
                                         'relationships': {'questions': {'data': [{'type': 'questions', 'id': '1'}]},
                                                           'next': {'data': []},
                                                           'prev': {'data': []},
                                                           'data_set': {'data': None}}},
                                'included': [{'type': 'questions',
                                              'id': '1',
                                              'attributes': {'order': 1,
                                                             'attributes': {'name': 'test_question',
                                                                            'title': 'Please provide some text'}},
                                              'relationships': {'q_type': {'data': {'type': 'question_types',
                                                                                    'id': '1'}}}},
                                             {'type': 'question_types',
                                                      'id': '1',
                                                      'attributes': {'name': 'text',
                                                                     'title': 'Static Text',
                                                                     'enabled': True,
                                                                     'order': 0,
                                                                     'frontend': {'text': '<p>Enter the text to display.</p>'},
                                                                     'backend': {'fields': []}},
                                                      'relationships': {'q_type_group': {'data': {'type': 'question_type_groups', 'id': '1'}}}},
                                             {'type': 'question_type_groups',
                                                      'id': '1',
                                                      'attributes': {'title': 'Builtin Questions',
                                                                     'name': 'ess:builtin',
                                                                     'order': 2,
                                                                     'enabled': True}}]})
    assert errors == {}
    assert page.name == 'test'
    assert page.title == 'Test Page'
    assert page.scripts == 'alert("");'
    assert page.styles == 'body {}'
    assert page.attributes == {'number_questions': True}
    assert len(page.questions) == 1
    assert page.questions[0].q_type.name == 'text'
    assert page.questions[0].q_type.q_type_group.name == 'ess:builtin'
    assert page.questions[0]['name'] == 'test_question'
    assert page.questions[0]['title'] == 'Please provide some text'
