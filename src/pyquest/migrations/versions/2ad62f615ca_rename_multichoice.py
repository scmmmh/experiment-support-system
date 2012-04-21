"""rename multichoice

Revision ID: 2ad62f615ca
Revises: 2b8fae7d7772
Create Date: 2012-04-21 12:48:39.950327

"""

# revision identifiers, used by Alembic.
revision = '2ad62f615ca'
down_revision = '2b8fae7d7772'

from alembic import op
import sqlalchemy as sa

questions = sa.sql.table('questions', 
                         sa.sql.column('type', sa.Unicode))

def upgrade():
    op.execute(questions.update().\
               where(questions.c.type==op.inline_literal('multichoice')).\
               values({'type': op.inline_literal('multi_choice')}))

def downgrade():
    op.execute(questions.update().\
               where(questions.c.type==op.inline_literal('multi_choice')).\
               values({'type': op.inline_literal('multichoice')}))
