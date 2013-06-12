"""create_data_item_list

Revision ID: 40af42e8f394
Revises: 1cd78b756fb3
Create Date: 2013-05-08 14:35:13.918437

"""

# revision identifiers, used by Alembic.
revision = '40af42e8f394'
down_revision = '315f2a8005ca'

from alembic import op

from sqlalchemy import (Column, ForeignKey, Integer, Unicode, Table, MetaData,
                        ForeignKey, and_)


metadata = MetaData()

qs = Table('qsheets', metadata,
           Column('id', Integer, primary_key=True),
           Column('name', Unicode(255)),
           Column('survey_id', Integer, ForeignKey('surveys.id')),
           Column('dataset_id', Integer))

di = Table('data_items', metadata,
           Column('id', Integer, primary_key=True),
           Column('dataset_id', Integer, ForeignKey('data_sets.id')),
           Column('qsheet_id', Integer, ForeignKey('qsheets.id')))

ds = Table('data_sets', metadata,
           Column('name', Unicode),
           Column('survey_id', Integer, ForeignKey('surveys.id')),
           Column('owned_by', Integer, ForeignKey('users.id')),
           Column('id', Integer, primary_key=True))

su = Table('surveys', metadata,
           Column('id', Integer, primary_key=True),
           Column('owned_by', Integer, ForeignKey('users.id')))

dk = Table('data_set_attribute_keys', metadata,
           Column('id', Integer, primary_key=True),
           Column('order', Integer),
           Column('key', Unicode),
           Column('dataset_id', Integer, ForeignKey('data_sets.id')))

da = Table('data_item_attributes', metadata,
           Column('id', Integer, primary_key=True),
           Column('data_item_id', Integer, ForeignKey('data_items.id')),
           Column('order', Integer),
           Column('value', Unicode),
           Column('key', Unicode))

# For each QSheet with DataItems attached the upgrade creates a new DataSet and moves the
# DataItems to that instead. The key column in data_item_attributes is no longer needed since the attributes are now
# identified by 'order' and the DataSet attribute keys.
def upgrade():
    op.create_table('data_sets',
                    Column('id', Integer, primary_key=True),
                    Column('name', Unicode(255)),
                    Column('survey_id', Integer, ForeignKey('surveys.id', name='data_sets_survey_id_fk')),
                    Column('owned_by', Integer, ForeignKey('users.id', name='data_sets_owned_by_fk')))

    op.create_table('data_set_attribute_keys',
                    Column('id', Integer, primary_key=True),
                    Column('order', Integer),
                    Column('key', Unicode(255)),
                    Column('dataset_id', Integer, ForeignKey('data_sets.id', name='data_set_attribute_keys_dataset_id_fk')))

    op.add_column('data_items',
                  Column('dataset_id', Integer, ForeignKey('data_sets.id', name='data_items_dataset_id_fk')))

    op.add_column('qsheets',
                  Column('dataset_id', Integer, ForeignKey('data_sets.id', name='qsheets_dataset_id_fk')))


    for qsheet in op.get_bind().execute(qs.select()):
        data_items = op.get_bind().execute(di.select().where(di.c.qsheet_id==qsheet.id))
        if data_items.rowcount > 0:
            survey = op.get_bind().execute(su.select().where(su.c.id==qsheet.survey_id)).first()
            ds_pk = op.get_bind().execute(ds.insert().values(name='created by migrations for qsheet %d' % qsheet.id, owned_by=survey.owned_by, survey_id=qsheet.survey_id)).inserted_primary_key[0]
            row = 1
            for data_item in data_items:
                op.get_bind().execute(di.update().where(di.c.id==data_item.id).values(dataset_id=ds_pk, qsheet_id=None))
                if row == 1:
                    attributes = op.get_bind().execute(da.select().where(da.c.data_item_id==data_item.id))
                    for attribute in attributes:
                        op.get_bind().execute(dk.insert().values(key=attribute.key, order=attribute.order, dataset_id=ds_pk))
                row = row + 1
            op.get_bind().execute(qs.update().where(qs.c.id==qsheet.id).values(dataset_id=ds_pk))

    op.drop_constraint('data_items_qsheet_id_fk', 'data_items', type_='foreignkey')
    op.drop_column('data_items', 'qsheet_id')
    op.drop_column('data_item_attributes', 'key')

# The downgrade moves the DataItems back from the DataSet to the relevant QSheet and restores the 'key' column of the DataItemAttributes.
def downgrade():
    op.add_column('data_items',
                  Column('qsheet_id', Integer, ForeignKey('qsheets.id', name='data_items_qsheet_id_fk')))

    op.add_column('data_item_attributes',
                  Column('key', Unicode(255)))

    op.drop_constraint('data_sets_owned_by_fk', 'data_sets', type='foreignkey')
    op.drop_constraint('data_sets_survey_id_fk', 'data_sets', type='foreignkey')
    op.drop_constraint('data_items_dataset_id_fk', 'data_items', type='foreignkey')
    op.drop_constraint('qsheets_dataset_id_fk', 'qsheets', type='foreignkey')
    op.drop_constraint('data_set_attribute_keys_dataset_id_fk', 'data_set_attribute_keys', type='foreignkey')

    for qsheet in op.get_bind().execute(qs.select()):
        if qsheet.dataset_id:
            data_set = op.get_bind().execute(ds.select().where(ds.c.id==qsheet.dataset_id)).first()
            data_items = op.get_bind().execute(di.select().where(di.c.dataset_id==qsheet.dataset_id))
            for data_item in data_items:
                op.get_bind().execute(di.update().where(di.c.id==data_item.id).values(dataset_id=None, qsheet_id=qsheet.id))
                for dia in op.get_bind().execute(da.select().where(da.c.data_item_id==data_item.id)):
                    new_key = op.get_bind().execute(dk.select().where(and_(dk.c.dataset_id==data_set.id, dk.c.order==dia.order))).first()['key']
                    op.get_bind().execute(da.update().where(da.c.id==dia.id).values(key=new_key))
            op.get_bind().execute(qs.update().where(qs.c.id==qsheet.id).values(dataset_id=None))
            op.get_bind().execute(ds.delete().where(ds.c.id==qsheet.dataset_id))

    op.drop_table('data_set_attribute_keys')
    op.drop_column('data_items', 'dataset_id')
    op.drop_column('qsheets', 'dataset_id')
    op.drop_table('data_sets')
