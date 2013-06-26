"""create_data_set_attribute_keys

Revision ID: 6e3dd1c4643
Revises: 444a8338869c
Create Date: 2013-06-25 15:10:32.981517

"""

# revision identifiers, used by Alembic.
revision = '6e3dd1c4643'
down_revision = '444a8338869c'

from alembic import op
from sqlalchemy import (Column, ForeignKey, Integer, Unicode, Table, MetaData,
                        ForeignKey, and_)
metadata = MetaData()

ds = Table('data_sets', metadata,
           Column('name', Unicode),
           Column('survey_id', Integer, ForeignKey('surveys.id')),
           Column('owned_by', Integer, ForeignKey('users.id')),
           Column('id', Integer, primary_key=True))

di = Table('data_items', metadata,
           Column('id', Integer, primary_key=True),
           Column('dataset_id', Integer, ForeignKey('data_sets.id')))

dk = Table('data_set_attribute_keys', metadata,
           Column('id', Integer, primary_key=True),
           Column('key', Unicode),
           Column('order', Integer),
           Column('dataset_id', Integer, ForeignKey('data_sets.id')))

da = Table('data_item_attributes', metadata,
           Column('id', Integer, primary_key=True),
           Column('data_item_id', Integer, ForeignKey('data_items.id')),
           Column('order', Integer),
           Column('value', Unicode),
           Column('key_id', Integer, ForeignKey('data_set_attribute_keys.id')),
           Column('key', Unicode))

def upgrade():
    op.create_table('data_set_attribute_keys',
                    Column('id', Integer, primary_key=True),
                    Column('key', Unicode(255)),
                    Column('order', Integer),
                    Column('dataset_id', Integer, ForeignKey('data_sets.id', name='data_set_attribute_keys_dataset_id_fk')))

    op.add_column('data_item_attributes',
                  Column('key_id', Integer, ForeignKey('data_set_attribute_keys.id', name='data_item_attributes_data_set_attribute_key_fk')))

    for dataset in op.get_bind().execute(ds.select()):
        data_items = op.get_bind().execute(di.select().where(di.c.dataset_id==dataset.id)).fetchall()
        if len(data_items) > 0:
            order = 1;
            for attribute in op.get_bind().execute(da.select().where(da.c.data_item_id==data_items[0].id)):
                op.get_bind().execute(dk.insert().values(key=attribute.key, dataset_id=dataset.id, order=order))
                order = order + 1
            for data_item in data_items:
                dias = op.get_bind().execute(da.select().where(da.c.data_item_id==data_item.id)).fetchall()
                for dia in dias:
                    dsak = op.get_bind().execute(dk.select().where(and_(dk.c.dataset_id==data_item.dataset_id, dk.c.key==dia.key))).first()
                    op.get_bind().execute(da.update().where(da.c.id==dia.id).values(key_id=dsak.id))

    op.drop_column('data_item_attributes', 'key')
    op.drop_column('data_item_attributes', 'order')


def downgrade():

    op.add_column('data_item_attributes', Column('key', Unicode(255)))
    op.add_column('data_item_attributes', Column('order', Integer))

    for dataset in op.get_bind().execute(ds.select()):
        data_items = op.get_bind().execute(di.select().where(di.c.dataset_id==dataset.id)).fetchall()
        for data_item in data_items:
            order = 1
            for dia in op.get_bind().execute(da.select().where(da.c.data_item_id==data_item.id)):
                dsak = op.get_bind().execute(dk.select().where(dk.c.id==dia.key_id)).first()
                op.get_bind().execute(da.update().where(da.c.id==dia.id).values(key=dsak.key, order=dsak.order))
                order = order + 1

    op.drop_constraint('data_set_attribute_keys_dataset_id_fk', 'data_set_attribute_keys', type='foreignkey')
    op.drop_constraint('data_item_attributes_data_set_attribute_key_fk', 'data_item_attributes', type='foreignkey')
    op.drop_column('data_item_attributes', 'key_id')
    op.drop_table('data_set_attribute_keys')

