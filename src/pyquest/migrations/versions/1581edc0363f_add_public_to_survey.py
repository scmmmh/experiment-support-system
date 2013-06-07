"""add_public_to_survey

Revision ID: 1581edc0363f
Revises: 315f2a8005ca
Create Date: 2013-06-07 19:06:44.932664

"""

# revision identifiers, used by Alembic.
revision = '1581edc0363f'
down_revision = '315f2a8005ca'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('surveys', sa.Column('public', sa.Boolean(), default=True))


def downgrade():
    op.drop_column('surveys', 'public')

