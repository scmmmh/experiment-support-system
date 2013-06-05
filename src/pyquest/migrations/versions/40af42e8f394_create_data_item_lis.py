"""create_data_item_list

Revision ID: 40af42e8f394
Revises: 1cd78b756fb3
Create Date: 2013-05-08 14:35:13.918437

"""

# revision identifiers, used by Alembic.
revision = '40af42e8f394'
down_revision = '1cd78b756fb3'

from alembic import op

from sqlalchemy import (Column, ForeignKey, Integer, Unicode, Table, MetaData,
                        ForeignKey, and_)

from migrate.changeset.constraint import ForeignKeyConstraint

metadata = MetaData()

#qs = Table('qsheets', metadata,
#           Column('id', Integer, primary_key=True),
#           Column('dataset_id', Integer))
#di = Table('data_items', metadata,
#           Column('id', Integer, primary_key=True),
#           Column('dataset_id', Integer, ForeignKey('data_sets.id')),
#           Column('qsheet_id', Integer, ForeignKey('qsheets.id')))
#ds = Table('data_sets', metadata,
#           Column('name', Unicode),
#           Column('id', Integer, primary_key=True))

def upgrade():
    op.create_table('data_sets',
                    Column('id', Integer, primary_key=True),
                    Column('name', VARCHAR(255)),
                    Column('owned_by', Integer, ForeignKey('users.id', name='data_sets_owned_by_fk')))

    op.add_column('data_items',
                  Column('dataset_id', Integer, ForeignKey('data_sets.id', name='data_items_dataset_id_fk')))

    # metadata.bind = op.get_bind()
    # # for each qsheet.id
    # for qsheet in op.get_bind().execute(qs.select()):
    # # look for data_items with that id
    #     data_items = op.get_bind().execute(di.select().where(di.c.qsheet_id==qsheet.id))
    # # if you find any:
    #     if data_items.rowcount > 0:
    # #    create a dataset
    #         ds_pk = op.get_bind().execute(ds.insert().values(name='created by migrations')).inserted_primary_key[0]
    # #    move the data_items in question to it
    #         for data_item in data_items:
    #             op.get_bind().execute(di.update().where(di.c.id==data_item.id).values(dataset_id=ds_pk, qsheet_id=None))
    # #    attach the dataset to the qsheet
    #         op.get_bind().execute(qs.update().where(qs.c.id==qsheet.id).values(dataset_id=ds_pk))

def downgrade():
    # # for each qsheet
    # for qsheet in op.get_bind().execute(qs.select()):
    # # if it has a dataset
    #     if qsheet.dataset_id:
    # # find the dataitems
    #         data_items = op.get_bind().execute(di.select().where(di.c.dataset_id==qsheet.dataset_id))
    # #    reattach its data_items to the relevant qsheet
    #         for data_item in data_items:
    #             op.get_bind().execute(di.update().where(di.c.id==data_item.id).values(dataset_id=None, qsheet_id=qsheet.id))
    # #    drop the dataset
    #         op.get_bind().execute(qs.update().where(qs.c.id==qsheet.id).values(dataset_id=None))
    #         op.get_bind().execute(ds.delete().where(ds.c.id==qsheet.dataset_id))

    op.drop_constraint('data_sets_owned_by_fk', 'data_sets', type='foreignkey')
    op.drop_constraint('data_items_dataset_id_fk', 'data_items', type='foreignkey')
    op.drop_column('data_items', 'dataset_id')
    op.drop_table('data_sets')
