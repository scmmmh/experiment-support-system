"""create permutations

Revision ID: 44a76d75263
Revises: 26adf3f9d0f5
Create Date: 2013-07-05 10:26:23.966556

"""

# revision identifiers, used by Alembic.
revision = '44a76d75263'
down_revision = '26adf3f9d0f5'

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

    op.create_table('permutations',
                    Column('id', Integer, primary_key=True),
                    Column('survey_id', Integer, ForeignKey('surveys.id', name='permutations_survey_fk')),
                    Column('applies_to', Integer, ForeignKey('qsheets.id', name='permutations_applies_to_fk')),
                    Column('dataset_id', Integer, ForeignKey('data_sets.id', name='permutations_dataset_id_fk')),
                    Column('assigned_to', Integer, ForeignKey('participants.id', name='permutations_participant_fk')))

def downgrade():
    op.drop_column('data_sets', 'type')
    op.drop_constraint('permutations_survey_fk', 'permutations', type='foreignkey')
    op.drop_constraint('permutations_applies_to_fk', 'permutations', type='foreignkey')
    op.drop_constraint('permutations_dataset_id_fk', 'permutations', type='foreignkey')
    op.drop_constraint('permutations_participant_fk', 'permutations', type='foreignkey')
    op.drop_table('permutations')
