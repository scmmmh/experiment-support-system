"""
##################
Move Data to Pages
##################

This revision moves the data-items, that were previously attached to
the Survey, to the QSheet. For each Survey it tries to find a QSheet that
has a "repeat" attribute value of "repeat" and will then use that as the
target QSheet. If such a QSheet does not exist, then a new one will be
added to the Survey.

Revision ID: 1341b5a7b155
Revises: 582fe131cec4
Create Date: 2012-09-13 09:05:05.114167
"""
from alembic import op
from sqlalchemy import (Column, Integer, Unicode, Table, MetaData,
                        ForeignKey, and_)


# revision identifiers, used by Alembic.
revision = '1341b5a7b155'
down_revision = '582fe131cec4'

metadata = MetaData()

qs = Table('qsheets', metadata,
           Column('id', Integer, primary_key=True),
           Column('survey_id', Integer))
qsa = Table('qsheet_attributes', metadata,
            Column('id', Integer, primary_key=True),
            Column('qsheet_id', Integer, ForeignKey(qs.c.id)),
            Column('key', Unicode),
            Column('value', Unicode))
di = Table('data_items', metadata,
           Column('id', Integer, primary_key=True),
           Column('survey_id', Integer),
           Column('qsheet_id', Integer))


def upgrade():
    metadata.bind = op.get_bind()
    op.add_column('data_items',
                  Column('qsheet_id', Integer, ForeignKey('qsheets.id', name='data_items_qsheet_id_fk')))
    for data_item in op.get_bind().execute(di.select()):
        qsheet = op.get_bind().execute(qs.join(qsa).select().where(and_(qs.c.survey_id == data_item.survey_id,
                                                                        qsa.c.key == 'repeat',
                                                                        qsa.c.value == 'repeat'))).first()
        if qsheet:
            qs_pk = qsheet[0]
        else:
            qs_pk = op.get_bind().execute(qs.insert().values(survey_id=data_item.survey_id)).inserted_primary_key[0]
            op.get_bind().execute(qsa.insert().values(qsheet_id=qs_pk,
                                                      key='repeat',
                                                      value='repeat'))
        op.get_bind().execute(di.update().where(di.c.id == data_item.id).values(qsheet_id=qs_pk))
    op.drop_column('data_items', 'survey_id')


def downgrade():
    metadata.bind = op.get_bind()
    op.add_column('data_items',
                  Column('survey_id', Integer, ForeignKey('surveys.id')))
    for data_item in op.get_bind().execute(di.select()):
        qsheet = op.get_bind().execute(qs.select().where(qs.c.id == data_item.qsheet_id)).first()
        op.get_bind().execute(di.update().where(di.c.id == data_item.id).values(survey_id=qsheet.survey_id))
    op.drop_constraint('data_items_qsheet_id_fk', 'data_items', type='foreignkey')
    op.drop_column('data_items', 'qsheet_id')
