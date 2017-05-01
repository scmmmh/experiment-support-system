"""
###################################################################
Change question attribute value columns from Unicode to UnicodeText
###################################################################

Revision ID: 23b66139a952
Revises: 488366bafc98
Create Date: 2013-03-10 18:34:04.565468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23b66139a952'
down_revision = '488366bafc98'


def upgrade():
    op.alter_column('question_attributes', 'value', type_=sa.UnicodeText, existing_type=sa.Unicode)
    op.alter_column('qsheet_attributes', 'value', type_=sa.UnicodeText, existing_type=sa.Unicode)


def downgrade():
    op.alter_column('question_attributes', 'value', type_=sa.Unicode(255), existing_type=sa.UnicodeText)
    op.alter_column('qsheet_attributes', 'value', type_=sa.Unicode(255), existing_type=sa.UnicodeText)
