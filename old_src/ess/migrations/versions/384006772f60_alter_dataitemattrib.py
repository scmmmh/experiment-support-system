"""Alter DataItemAttribute to use UnicodeText, allowing for essentially arbitrary
length data item values.

Revision ID: 384006772f60
Revises: 26adf3f9d0f5
Create Date: 2013-08-15 12:49:18.722339
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '384006772f60'
down_revision = '26adf3f9d0f5'


def upgrade():
    op.alter_column('data_item_attributes', 'value', type_=sa.UnicodeText)


def downgrade():
    op.alter_column('data_item_attributes', 'value', type_=sa.Unicode(255))
