"""
###################
Rename rating_group
###################

Revision ID: 57962be6396b
Revises: 2ad62f615ca
Create Date: 2012-04-22 17:58:36.163338
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '57962be6396b'
down_revision = '2ad62f615ca'

questions = sa.sql.table('questions',
                         sa.sql.column('type', sa.Unicode))


def upgrade():
    op.execute(questions.update().
               where(questions.c.type == op.inline_literal('rating_group')).
               values({'type': op.inline_literal('single_choice_grid')}))


def downgrade():
    op.execute(questions.update().
               where(questions.c.type == op.inline_literal('single_choice_grid')).
               values({'type': op.inline_literal('rating_group')}))
