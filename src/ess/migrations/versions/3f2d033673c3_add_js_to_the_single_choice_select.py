'''
##################################
Add JS to the Single Choice Select
##################################

Revision ID: 3f2d033673c3
Revises: d7a914dbc133
Create Date: 2017-11-20 11:19:33.237693
'''
import json

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3f2d033673c3'
down_revision = 'd7a914dbc133'

metadata = sa.MetaData()

question_type_groups = sa.Table('question_type_groups', metadata,
                                sa.Column('id', sa.Integer(), primary_key=True),
                                sa.Column('name', sa.Unicode(255)),
                                sa.Column('parent_id', sa.Integer()))
question_types = sa.Table('question_types', metadata,
                          sa.Column('id', sa.Integer(), primary_key=True),
                          sa.Column('name', sa.Unicode(255)),
                          sa.Column('frontend', sa.UnicodeText()),
                          sa.Column('group_id', sa.Integer()))

OLD_FRONTEND = {'display_as': 'select_simple_choice',
                'generates_response': True,
                'visible': True,
                'width': 'small-12',
                'widget': 'list',
                'answers': []}
NEW_FRONTEND = {'display_as': 'select_simple_choice',
                'generates_response': True,
                'visible': True,
                'width': 'small-12',
                'widget': 'list',
                'answers': [],
                'javascript': "if(question.find('input.other-option-text').length > 0) {var mode = question.find('select').length > 0 ? 'select' : 'input';function update_other() {if(mode == 'select') {if(question.find('select').val().indexOf('other') >= 0) {question.find('input.other-option-text').parent().show();} else {question.find('input.other-option-text').parent().hide();}} else {if(question.find('input[type=checkbox], input[type=radio]').filter('input[value=other]:checked').length > 0) {question.find('input.other-option-text').parent().show();} else {question.find('input.other-option-text').parent().hide();}}}update_other();question.find('select, input[type=checkbox], input[type=radio]').on('change', update_other);}"}  # noqa: E501


def upgrade():
    metadata.bind = op.get_bind()
    builtins = op.get_bind().execute(question_type_groups.select().
                                     where(question_type_groups.c.name == 'ess:builtins')).first()
    core = op.get_bind().execute(question_type_groups.select().
                                 where(sa.and_(question_type_groups.c.name == 'ess:core',
                                               question_type_groups.c.parent_id == builtins[0]))).first()
    op.get_bind().execute(question_types.update().values(frontend=json.dumps(NEW_FRONTEND)).
                          where(sa.and_(question_types.c.name == 'select_simple_choice',
                                        question_types.c.group_id == core[0])))


def downgrade():
    metadata.bind = op.get_bind()
    builtins = op.get_bind().execute(question_type_groups.select().
                                     where(question_type_groups.c.name == 'ess:builtins')).first()
    core = op.get_bind().execute(question_type_groups.select().
                                 where(sa.and_(question_type_groups.c.name == 'ess:core',
                                               question_type_groups.c.parent_id == builtins[0]))).first()
    op.get_bind().execute(question_types.update().values(frontend=json.dumps(OLD_FRONTEND)).
                          where(sa.and_(question_types.c.name == 'select_simple_choice',
                                        question_types.c.group_id == core[0])))
