"""create permutations

Revision ID: 44a76d75263
Revises: 26adf3f9d0f5
Create Date: 2013-07-05 10:26:23.966556

"""

# revision identifiers, used by Alembic.
revision = '44a76d75263'
down_revision = '384006772f60'

from alembic import op
from sqlalchemy import Column, Integer, Unicode, ForeignKey, MetaData, Table, Boolean

metadata = MetaData()

ds = Table('data_sets', metadata,
           Column('name', Unicode),
           Column('survey_id', Integer, ForeignKey('surveys.id')),
           Column('owned_by', Integer, ForeignKey('users.id')),
           Column('id', Integer, primary_key=True),
           Column('type', Unicode))

def upgrade():
    op.add_column('data_sets', Column('type', Unicode(20)))
    op.add_column('data_sets', Column('show_in_list', Boolean))
    # Is this correct? These are the columns for PermutationSet which is extended from
    # DataSet and uses the same table.
    op.add_column('data_sets', Column('paramstring', Unicode(255)))
    op.add_column('data_sets', Column('applies_to', Unicode(255)))
    op.add_column('data_sets', Column('tasks', Unicode(255)))
    op.add_column('data_sets', Column('interfaces', Unicode(255)))

    for dataset in op.get_bind().execute(ds.select()):
        op.get_bind().execute(ds.update().values({'type':'dataset'}))

    op.add_column('participants', Column('permutation_id', Integer))
    op.add_column('participants', Column('permutation_qsheet_id',Unicode(20)))


def downgrade():
    op.drop_column('data_sets', 'type')
    op.drop_column('data_sets', 'show_in_list')
    op.drop_column('data_sets', 'paramstring')
    op.drop_column('data_sets', 'applies_to')
    op.drop_column('data_sets', 'tasks')
    op.drop_column('data_sets', 'interfaces')

    op.drop_column('participants', 'permutation_id')
    op.drop_column('participants', 'permutation_qsheet_id')
