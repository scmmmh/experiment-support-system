"""
#####################
Add participant state
#####################

Revision ID: 444a8338869c
Revises: 17c68d338ee4
Create Date: 2013-06-09 10:52:39.039875
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '444a8338869c'
down_revision = '1581edc0363f'


def upgrade():
    op.add_column('participants',
                  sa.Column('state', sa.UnicodeText))


def downgrade():
    op.drop_column('participants', 'state')
