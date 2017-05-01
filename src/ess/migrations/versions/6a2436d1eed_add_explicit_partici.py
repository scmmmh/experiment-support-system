"""
################################################
Add explicit participant - permutation item link
################################################

Revision ID: 6a2436d1eed
Revises: 5008e04b83bb
Create Date: 2014-01-19 15:45:09.538551

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6a2436d1eed'
down_revision = '5008e04b83bb'


def upgrade():
    op.add_column('participants',
                  sa.Column('permutation_item_id',
                            sa.Integer,
                            sa.ForeignKey('data_items.id', name='participants_data_set_item_id_perm_fk')))


def downgrade():
    op.drop_constraint('participants_data_set_item_id_perm_fk', 'participants', type_='foreignkey')
    op.drop_column('participants', 'permutation_item_id')
