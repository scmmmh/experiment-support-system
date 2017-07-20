"""
#####################################################
Enable the backend for random question / answer order
#####################################################

Revision ID: d7a914dbc133
Revises: 93591ffbbc1b
Create Date: 2017-07-20 19:53:58.771440

"""
import json

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd7a914dbc133'
down_revision = '93591ffbbc1b'

metadata = sa.MetaData()
question_type_groups = sa.Table('question_type_groups', metadata,
                                sa.Column('id', sa.Integer(), primary_key=True),
                                sa.Column('name', sa.Unicode(255)),
                                sa.Column('parent_id', sa.Integer()))
question_types = sa.Table('question_types', metadata,
                          sa.Column('id', sa.Integer(), primary_key=True),
                          sa.Column('name', sa.Unicode(255)),
                          sa.Column('frontend', sa.UnicodeText()),
                          sa.Column('backend', sa.UnicodeText()),
                          sa.Column('group_id', sa.Integer()),
                          sa.Column('parent_id', sa.Integer()))


def upgrade():
    parent = op.get_bind().execute(question_type_groups.select().where(question_type_groups.c.name == 'ess:builtins')).first()
    parent = op.get_bind().execute(question_type_groups.select().where(sa.and_(question_type_groups.c.name == 'ess:core',
                                                                               question_type_groups.c.parent_id == parent[0]))).first()
    for qt in op.get_bind().execute(question_types.select().where(sa.and_(question_types.c.group_id == parent[0],
                                                                          question_types.c.name.in_(['select_simple_choice', 'select_grid_choice', 'ranking'])))):
        backend = json.loads(qt[3])
        if qt[1] == 'select_grid_choice':
            backend['fields'].append({'title': 'Randomise the question order',
                                      'name': 'randomise_questions',
                                      'validation': {'type': 'boolean',
                                                     'if_empty': False,
                                                     'if_missing': False},
                                      'type': 'checkbox'})
        backend['fields'].append({'title': 'Randomise the answer order',
                                  'name': 'randomise_answers',
                                  'validation': {'type': 'boolean',
                                                 'if_empty': False,
                                                 'if_missing': False},
                                  'type': 'checkbox'})
        backend = json.dumps(backend)
        op.get_bind().execute(question_types.update().values(backend=backend).where(question_types.c.id == qt[0]))


def downgrade():
    parent = op.get_bind().execute(question_type_groups.select().where(question_type_groups.c.name == 'ess:builtins')).first()
    parent = op.get_bind().execute(question_type_groups.select().where(sa.and_(question_type_groups.c.name == 'ess:core',
                                                                               question_type_groups.c.parent_id == parent[0]))).first()
    for qt in op.get_bind().execute(question_types.select().where(sa.and_(question_types.c.group_id == parent[0],
                                                                          question_types.c.name.in_(['select_simple_choice', 'select_grid_choice', 'ranking'])))):
        backend = json.loads(qt[3])
        backend['fields'] = [f for f in backend['fields'] if f['name'] not in ['randomise_questions', 'randomise_answers']]
        backend = json.dumps(backend)
        op.get_bind().execute(question_types.update().values(backend=backend).where(question_types.c.id == qt[0]))
