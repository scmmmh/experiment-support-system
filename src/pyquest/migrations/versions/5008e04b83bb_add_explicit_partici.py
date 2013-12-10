"""Add explicit participant completed flag

Revision ID: 5008e04b83bb
Revises: 4c876b48f28b
Create Date: 2013-12-10 19:54:12.582936

"""

# revision identifiers, used by Alembic.
revision = '5008e04b83bb'
down_revision = '4c876b48f28b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('participants', sa.Column('completed', sa.Boolean))


def downgrade():
    op.drop_column('participants', 'completed')
