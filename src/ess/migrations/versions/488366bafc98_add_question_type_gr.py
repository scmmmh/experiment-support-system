"""Add question type groups

Revision ID: 488366bafc98
Revises: 25b3de3526f
Create Date: 2013-01-06 18:39:37.037112

"""

# revision identifiers, used by Alembic.
revision = '488366bafc98'
down_revision = '25b3de3526f'

from alembic import op
import sqlalchemy as sa

metadata = sa.MetaData()

qt = sa.Table('question_types', metadata,
              sa.Column('id', sa.Integer, primary_key=True),
              sa.Column('group_id', sa.Unicode(255)))
qtg = sa.Table('question_type_groups', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.Unicode(255), unique=True),
               sa.Column('title', sa.Unicode(255)),
               sa.Column('order', sa.Integer))

def upgrade():
    metadata.bind = op.get_bind()
    op.create_table('question_type_groups',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.Unicode(255), unique=True),
                    sa.Column('title', sa.Unicode(255)),
                    sa.Column('order', sa.Integer))
    op.add_column('question_types', sa.Column('group_id', sa.Integer, sa.ForeignKey('question_type_groups.id', name='question_type_groups_fk')))
    qtg_pk = op.get_bind().execute(qtg.insert().values(name=u'core', title=u'Core Questions', order=0)).inserted_primary_key[0]
    op.execute(qt.update().values({u'group_id': qtg_pk}))

def downgrade():
    op.drop_constraint('question_type_groups_fk', 'question_types', type='foreignkey')
    op.drop_column('question_types', 'group_id')
    op.drop_table('question_type_groups')
