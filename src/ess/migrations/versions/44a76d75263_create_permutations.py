"""create permutations

Revision ID: 44a76d75263
Revises: 26adf3f9d0f5
Create Date: 2013-07-05 10:26:23.966556

"""

# revision identifiers, used by Alembic.
revision = '44a76d75263'
down_revision = '384006772f60'

from alembic import op
import sqlalchemy as sa

metadata = sa.MetaData()

ds = sa.Table('data_sets', metadata,
           sa.Column('name', sa.Unicode),
           sa.Column('survey_id', sa.Integer, sa.ForeignKey('surveys.id')),
           sa.Column('owned_by', sa.Integer, sa.ForeignKey('users.id')),
           sa.Column('id', sa.Integer, primary_key=True),
           sa.Column('type', sa.Unicode))

def upgrade():
    op.add_column('data_sets', sa.Column('type', sa.Unicode(20)))

    for dataset in op.get_bind().execute(ds.select()):
        op.get_bind().execute(ds.update().values({'type':'dataset'}))

    op.create_table('data_set_relations',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('subject_id', sa.Integer, sa.ForeignKey('data_sets.id', name='data_set_relations_subject_id_fk')),
                    sa.Column('object_id', sa.Integer, sa.ForeignKey('data_sets.id', name='data_set_relations_object_id_fk')),
                    sa.Column('rel', sa.Unicode(255)),
                    sa.Column('_data', sa.UnicodeText))

def downgrade():
    op.drop_table('data_set_relations')
    op.drop_column('data_sets', 'type')
