"""create permutations

Revision ID: 44a76d75263
Revises: 26adf3f9d0f5
Create Date: 2013-07-05 10:26:23.966556

"""

# revision identifiers, used by Alembic.
revision = '44a76d75263'
down_revision = '384006772f60'

from alembic import op
from sqlalchemy import Column, Integer, Unicode, ForeignKey, MetaData, Table

metadata = MetaData()

ds = Table('data_sets', metadata,
           Column('name', Unicode),
           Column('survey_id', Integer, ForeignKey('surveys.id')),
           Column('owned_by', Integer, ForeignKey('users.id')),
           Column('id', Integer, primary_key=True),
           Column('type', Unicode))

def upgrade():
    op.add_column('data_sets', Column('type', Unicode(20)))
    for dataset in op.get_bind().execute(ds.select()):
        op.get_bind().execute(ds.update().values({'type':'dataset'}))

def downgrade():
    op.drop_column('data_sets', 'type')
