"""add_questionnaire_language

Revision ID: b83f6a6695c
Revises: None
Create Date: 2012-04-06 15:55:40.422771

"""

# revision identifiers, used by Alembic.
revision = 'b83f6a6695c'
down_revision = None

from alembic import op
from sqlalchemy import Column, Unicode


def upgrade():
    op.add_column('surveys',
                  Column('language', Unicode))


def downgrade():
    op.drop_column('surveys', 'language')
