"""
################
Add user options
################

Revision ID: 7f8cc2026730
Revises: 637675a9afd3
Create Date: 2016-12-18 13:22:04.888822

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7f8cc2026730'
down_revision = '637675a9afd3'


def upgrade():
    op.add_column('users', sa.Column('options', sa.UnicodeText))


def downgrade():
    op.drop_column('users', 'options')
