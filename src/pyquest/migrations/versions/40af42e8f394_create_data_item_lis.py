"""create_data_item_list

Revision ID: 40af42e8f394
Revises: c6ce6d3adb3
Create Date: 2013-05-08 14:35:13.918437

"""

# revision identifiers, used by Alembic.
revision = '40af42e8f394'
down_revision = 'c6ce6d3adb3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('data_item_sets',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.VARCHAR(255)))

    op.add_column('data_items',
                  sa.Column('data_item_set_id', sa.Integer, sa.ForeignKey('data_item_sets.id')))

def downgrade():
    op.drop_constraint('data_items_ibfk_2', 'data_items', 'foreignkey')
    op.drop_column('data_items', 'data_item_set_id')
    op.drop_table('data_item_sets')
