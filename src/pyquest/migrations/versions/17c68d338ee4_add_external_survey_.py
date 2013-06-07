"""Add external survey id

Revision ID: 17c68d338ee4
Revises: 1cd78b756fb3
Create Date: 2013-06-04 19:43:15.101296

"""

# revision identifiers, used by Alembic.
revision = '17c68d338ee4'
down_revision = '1cd78b756fb3'

from alembic import op
from uuid import uuid1
import sqlalchemy as sa


s_table = sa.sql.table('surveys',
                       sa.sql.column('id', sa.Integer),
                       sa.sql.column('external_id', sa.Unicode(64)))

def upgrade():
    op.add_column('surveys', sa.Column('external_id', sa.Unicode(64)))
    op.create_index('ix_surveys_external_id', table_name='surveys', columns=['external_id'])
    for survey in op.get_bind().execute(s_table.select()):
        op.get_bind().execute(s_table.update().values(external_id=unicode(uuid1(clock_seq=survey[0]).hex)).where(s_table.c.id==survey[0]))

def downgrade():
    op.drop_column('surveys', 'external_id')
