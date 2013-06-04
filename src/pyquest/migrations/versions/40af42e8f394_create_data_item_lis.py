"""create_data_item_list

Revision ID: 40af42e8f394
Revises: 1cd78b756fb3
Create Date: 2013-05-08 14:35:13.918437

"""

# revision identifiers, used by Alembic.
revision = '40af42e8f394'
down_revision = '1cd78b756fb3'

from alembic import op
import sqlalchemy as sa
from migrate.changeset.constraint import ForeignKeyConstraint

def upgrade():
    op.create_table('data_sets',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.VARCHAR(255)),
                    sa.Column('owned_by', sa.Integer, sa.ForeignKey('users.id')),
                    sa.Column('qsheet_id', sa.Integer, sa.ForeignKey('qsheets.id')))

    op.add_column('data_items',
                  sa.Column('dataset_id', sa.Integer, sa.ForeignKey('data_sets.id')))

def downgrade():
    constraint = ForeignKeyConstraint('data_item_sets.owned_by', 'users.id')
    constraint.drop()
    op.drop_constraint('data_item_sets_ibfk_2', 'data_item_sets', 'foreignkey')
    op.drop_constraint('data_items_ibfk_1', 'data_items', 'foreignkey')
    op.drop_column('data_items', 'dataset_id')
    op.drop_table('data_item_sets')
