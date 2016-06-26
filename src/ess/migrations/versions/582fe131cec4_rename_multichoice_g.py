"""rename multichoice_group

Revision ID: 582fe131cec4
Revises: 57962be6396b
Create Date: 2012-04-22 18:21:51.764203

"""

# revision identifiers, used by Alembic.
revision = '582fe131cec4'
down_revision = '57962be6396b'

from alembic import op
import sqlalchemy as sa

questions = sa.sql.table('questions', 
                         sa.sql.column('type', sa.Unicode))

def upgrade():
    op.execute(questions.update().\
               where(questions.c.type==op.inline_literal('multichoice_group')).\
               values({'type': op.inline_literal('multi_choice_grid')}))

def downgrade():
    op.execute(questions.update().\
               where(questions.c.type==op.inline_literal('multi_choice_grid')).\
               values({'type': op.inline_literal('multichoice_group')}))
