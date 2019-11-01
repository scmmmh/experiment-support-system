"""
#############################
Add question-type inheritance
#############################

Revision ID: 64ef6deb982
Revises: 33d37cab0f8a
Create Date: 2013-04-20 17:15:25.552671
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '64ef6deb982'
down_revision = '33d37cab0f8a'


def upgrade():
    op.add_column('question_types',
                  sa.Column('parent_id', sa.Integer, sa.ForeignKey('question_types.id',
                                                                   name='question_types_parent_fk')))


def downgrade():
    op.drop_constraint('question_types_parent_fk', 'question_types', type='foreignkey')
    op.drop_column('question_types', 'parent_id')
