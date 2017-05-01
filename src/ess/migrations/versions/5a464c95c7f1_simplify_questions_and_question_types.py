"""
#####################################
Simplify Questions and Question Types
#####################################

Revision ID: 5a464c95c7f1
Revises: 11b7c2763658
Create Date: 2016-05-08 19:13:21.079496
"""
import json
import sqlalchemy as sa

from alembic import op
from babel import Locale

# revision identifiers, used by Alembic.
revision = '5a464c95c7f1'
down_revision = '11b7c2763658'

metadata = sa.MetaData()

question_types = sa.Table('question_types', metadata,
                          sa.Column('id', sa.Integer, primary_key=True),
                          sa.Column('name', sa.Unicode),
                          sa.Column('attributes', sa.UnicodeText))
questions = sa.Table('questions', metadata,
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('type_id', sa.Integer),
                     sa.Column('name', sa.Unicode),
                     sa.Column('required', sa.Boolean),
                     sa.Column('attributes', sa.UnicodeText))
questions_attr_group = sa.Table('question_complex_attributes', metadata,
                                sa.Column('id', sa.Integer, primary_key=True),
                                sa.Column('question_id', sa.Integer),
                                sa.Column('key', sa.Unicode),
                                sa.Column('order', sa.Integer))
questions_attr = sa.Table('question_attributes', metadata,
                          sa.Column('id', sa.Integer, primary_key=True),
                          sa.Column('question_group_id', sa.Integer),
                          sa.Column('key', sa.Unicode),
                          sa.Column('value', sa.Unicode),
                          sa.Column('order', sa.Integer))


def upgrade():
    locale = Locale('en')
    languages = list(locale.languages.items())
    languages.sort(key=lambda t: t[1])
    territories = list(locale.territories.items())
    territories.sort(key=lambda t: t[1])
    metadata.bind = op.get_bind()
    # Add the new columns
    op.add_column('question_types', sa.Column('attributes', sa.UnicodeText))
    op.add_column('questions', sa.Column('attributes', sa.UnicodeText))
    # Update the question types
    question_type_mapping = {}
    for question_type in op.get_bind().execute(question_types.select()):
        question_type_mapping[question_type[0]] = question_type[1]
        attrs = {}
        if question_type[1] == 'text':
            attrs = {'display_as': 'text',
                     'width': 'small-12',
                     'user_input': False,
                     'visible': True}
        elif question_type[1] in ['long_text', 'short_text', 'number', 'email',
                                  'url', 'date', 'time', 'datetime', 'month']:
            input_type = question_type[1]
            if input_type == 'short_text':
                input_type = 'text'
            elif input_type == 'long_text':
                input_type = 'textarea'
            attrs = {'display_as': 'simple_input',
                     'input_type': input_type,
                     'width': 'small-12 medium-8 large-6',
                     'user_input': True,
                     'visible': True}
        elif question_type[1] in ['single_choice', 'multi_choice']:
            attrs = {'display_as': 'select_simple_choice',
                     'allow_multiple': False if question_type[1] == 'single_choice' else True,
                     'widget': 'list',
                     'width': 'small-12 medium-8 large-6',
                     'user_input': True,
                     'visible': True,
                     'answers': []}
        elif question_type[1] == 'confirm':
            attrs = {'display_as': 'simple_input',
                     'input_type': 'checkbox',
                     'label': '',
                     'width': 'small-12 medium-8 large-6',
                     'user_input': True,
                     'visible': True}
        elif question_type[1] == 'page_timer':
            attrs = {'display_as': 'simple_input',
                     'input_type': 'hidden',
                     'user_input': True,
                     'visible': False}
        elif question_type[1] == 'hidden_value':
            attrs = {'display_as': 'simple_input',
                     'input_type': 'hidden',
                     'user_input': True,
                     'visible': False}
        elif question_type[1] == 'auto_commit':
            attrs = {'display_as': 'simple_input',
                     'input_type': 'hidden',
                     'user_input': False,
                     'visible': False}
        elif question_type[1] in ['single_choice_grid', 'multi_choice_grid']:
            attrs = {'display_as': 'select_grid_choice',
                     'allow_multiple': False if question_type[1] == 'single_choice_grid' else True,
                     'width': 'small-12',
                     'user_input': True,
                     'visible': True,
                     'answers': [],
                     'questions': []}
        elif question_type[1] == 'ranking':
            attrs = {'display_as': 'ranking',
                     'width': 'small-12 medium-8 large-6',
                     'user_input': True,
                     'visible': True,
                     'answers': []}
        elif question_type[1] == 'language':
            attrs = {'display_as': 'select_simple_choice',
                     'allow_multiple': False,
                     'widget': 'select',
                     'width': 'small-12 medium-8 large-6',
                     'user_input': True,
                     'visible': True,
                     'answers': [{'value': language[0], 'label': language[1]} for language in languages]}
        elif question_type[1] == 'country':
            attrs = {'display_as': 'select_simple_choice',
                     'allow_multiple': False,
                     'widget': 'select',
                     'width': 'small-12 medium-8 large-6',
                     'user_input': True,
                     'visible': True,
                     'answers': [{'value': territory[0], 'label': territory[1]} for territory in territories]}
        elif question_type[1] == 'js_check':
            attrs = {'display_as': 'js_check',
                     'user_input': False,
                     'visible': False}
        op.execute(question_types.update().
                   where(question_types.c.id == question_type[0]).values({'attributes': json.dumps(attrs)}))
    # Update the questions
    for question in op.get_bind().execute(questions.select()):
        attributes = op.get_bind().execute(questions_attr_group.
                                           join(questions_attr,
                                                questions_attr_group.c.id == questions_attr.c.question_group_id).
                                           select().where(questions_attr_group.c.question_id == question[0]).
                                           order_by(questions_attr_group.c.order,
                                                    questions_attr.c.order,
                                                    questions_attr.c.key))
        question_type = question_type_mapping[question[1]]
        attrs = {'required': question[3]}
        if question_type_mapping[question[1]] == 'text':
            for source_attr in attributes:
                if source_attr[2] == 'text' and source_attr[6] == 'text':
                    attrs['text'] = source_attr[7]
        elif question_type_mapping[question[1]] == 'long_text':
            attrs['input_type'] = 'textarea'
        elif question_type_mapping[question[1]] == 'short_text':
            attrs['input_type'] = 'text'
        elif question_type_mapping[question[1]] in ['number', 'email', 'url', 'date', 'time', 'datetime', 'month']:
            attrs['input_type'] = question_type_mapping[question[1]]
            for source_attr in attributes:
                if source_attr[2] == 'further' and source_attr[6] in ['min', 'max']:
                    if 'extra_args' not in attrs:
                        attrs['extra_args'] = {}
                    attrs['extra_args'][source_attr[6]] = source_attr[7]
        elif question_type_mapping[question[1]] in ['single_choice', 'multi_choice']:
            attrs['allow_multiple'] = False if question_type_mapping[question[1]] == 'single_choice' else True
            attrs['answers'] = []
            answer = {}
            for source_attr in attributes:
                if source_attr[2] == 'further' and source_attr[6] == 'subtype':
                    attrs['widget'] = source_attr[7]
                elif source_attr[2] == 'further' and source_attr[6] == 'allow_other':
                    attrs['allow_other'] = True if source_attr[7].lower() == 'single' else False
                elif source_attr[2] == 'further' and source_attr[6] == 'before_label':
                    attrs['before_label'] = source_attr[7]
                elif source_attr[2] == 'further' and source_attr[6] == 'after_label':
                    attrs['after_label'] = source_attr[7]
                elif source_attr[2] == 'answer' and source_attr[6] == 'value':
                    answer = {'value': source_attr[7]}
                elif source_attr[2] == 'answer' and source_attr[6] == 'label':
                    answer['label'] = source_attr[7]
                    attrs['answers'].append(answer)
        elif question_type_mapping[question[1]] == 'confirm':
            for source_attr in attributes:
                if source_attr[2] == 'further' and source_attr[6] == 'label':
                    attrs['label'] = source_attr[7]
                elif source_attr[2] == 'further' and source_attr[6] == 'value':
                    attrs['value'] = source_attr[7]
        elif question_type_mapping[question[1]] == 'hidden_value':
            for source_attr in attributes:
                if source_attr[2] == 'further' and source_attr[6] == 'value':
                    attrs['value'] = source_attr[7]
        elif question_type_mapping[question[1]] == 'auto_commit':
            for source_attr in attributes:
                if source_attr[2] == 'further' and source_attr[6] == 'timeout':
                    attrs['value'] = source_attr[7]
        elif question_type_mapping[question[1]] in ['single_choice_grid', 'multi_choice_grid']:
            attrs['allow_multiple'] = False if question_type_mapping[question[1]] == 'single_choice' else True
            attrs['answers'] = []
            attrs['questions'] = []
            answer = {}
            subquestion = {}
            for source_attr in attributes:
                if source_attr[2] == 'further' and source_attr[6] == 'before_label':
                    attrs['before_label'] = source_attr[7]
                elif source_attr[2] == 'further' and source_attr[6] == 'after_label':
                    attrs['after_label'] = source_attr[7]
                elif source_attr[2] == 'answer' and source_attr[6] == 'value':
                    answer = {'value': source_attr[7]}
                elif source_attr[2] == 'answer' and source_attr[6] == 'label':
                    answer['label'] = source_attr[7]
                    attrs['answers'].append(answer)
                elif source_attr[2] == 'subquestion' and source_attr[6] == 'name':
                    subquestion = {'name': source_attr[7]}
                elif source_attr[2] == 'subquestion' and source_attr[6] == 'label':
                    subquestion['label'] = source_attr[7]
                    attrs['questions'].append(subquestion)
        elif question_type_mapping[question[1]] == 'ranking':
            attrs['answers'] = []
            answer = {}
            for source_attr in attributes:
                if source_attr[2] == 'answer' and source_attr[6] == 'value':
                    answer = {'value': source_attr[7]}
                elif source_attr[2] == 'answer' and source_attr[6] == 'label':
                    answer['label'] = source_attr[7]
                    attrs['answers'].append(answer)
        elif question_type_mapping[question[1]] in ['language', 'country']:
            for source_attr in attributes:
                if source_attr[2] == 'further' and source_attr[6] == 'allow_multiple':
                    attrs['allow_multiple'] = True if source_attr[7].lower() == 'true' else False
                elif source_attr[2] == 'answer' and source_attr[6] == 'label':
                    attrs['prioritise'] = [value.strip() for value in source_attr[7].split(',')]
        op.execute(questions.update().
                   where(questions.c.id == question[0]).values({'attributes': json.dumps(attrs)}))


def downgrade():
    metadata.bind = op.get_bind()
    op.drop_column('questions', 'attributes')
    op.drop_column('question_types', 'attributes')
