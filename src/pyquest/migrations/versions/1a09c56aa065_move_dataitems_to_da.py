"""move_dataitems_to_dataset

Revision ID: 1a09c56aa065
Revises: 40af42e8f394
Create Date: 2013-06-04 16:15:28.622051

"""

# revision identifiers, used by Alembic.
revision = '1a09c56aa065'
down_revision = '40af42e8f394'

from alembic import op
import sqlalchemy as sa

from sqlalchemy import (Column, ForeignKey, Integer, Unicode, Table, MetaData,
                        ForeignKey, and_)

metadata = MetaData()

qs = Table('qsheets', metadata,
           Column('id', Integer, primary_key=True),
           Column('dataset_id', Integer))
di = Table('data_items', metadata,
           Column('id', Integer, primary_key=True),
           Column('dataset_id', Integer, ForeignKey('data_sets.id')),
           Column('qsheet_id', Integer, ForeignKey('qsheets.id')))
ds = Table('data_sets', metadata,
           Column('name', Unicode),
           Column('id', Integer, primary_key=True))

def upgrade():
    metadata.bind = op.get_bind()
    # for each qsheet.id
    for qsheet in op.get_bind().execute(qs.select()):
    # look for data_items with that id
        data_items = op.get_bind().execute(di.select().where(di.c.qsheet_id==qsheet.id))
    # if you find any:
        if data_items.rowcount > 0:
    #    create a dataset
            ds_pk = op.get_bind().execute(ds.insert().values(name='created by migrations')).inserted_primary_key[0]
    #    move the data_items in question to it
            for data_item in data_items:
                op.get_bind().execute(di.update().where(di.c.id==data_item.id).values(dataset_id=ds_pk, qsheet_id=None))
    #    attach the dataset to the qsheet
            op.get_bind().execute(qs.update().where(qs.c.id==qsheet.id).values(dataset_id=ds_pk))

def downgrade():
    # for each qsheet
    for qsheet in op.get_bind().execute(qs.select()):
    # if it has a dataset
        if qsheet.dataset_id:
    # find the dataitems
            data_items = op.get_bind().execute(di.select().where(di.c.dataset_id==qsheet.dataset_id))
    #    reattach its data_items to the relevant qsheet
            for data_item in data_items:
                op.get_bind().execute(di.update().where(di.c.id==data_item.id).values(dataset_id=None, qsheet_id=qsheet.id))
    #    drop the dataset
            op.get_bind().execute(qs.update().where(qs.c.id==qsheet.id).values(dataset_id=None))
            op.get_bind().execute(ds.delete().where(ds.c.id==qsheet.dataset_id))
            
