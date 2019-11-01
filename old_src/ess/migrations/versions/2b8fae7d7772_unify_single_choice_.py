"""
#############################
Unify single choice questions
#############################

Revision ID: 2b8fae7d7772
Revises: b83f6a6695c
Create Date: 2012-04-20 18:04:10.509801
"""
from alembic import op
from sqlalchemy import Unicode, Integer, Column, Table, MetaData, and_


# revision identifiers, used by Alembic.
revision = '2b8fae7d7772'
down_revision = 'b83f6a6695c'

metadata = MetaData()
questions = Table('questions', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('type', Unicode))
qca = Table('question_complex_attributes', metadata,
            Column('id', Integer, primary_key=True),
            Column('question_id', Integer),
            Column('key', Unicode),
            Column('label', Unicode),
            Column('order', Integer))
qa = Table('question_attributes', metadata,
           Column('id', Integer, primary_key=True),
           Column('question_group_id', Integer),
           Column('key', Unicode),
           Column('label', Unicode),
           Column('value', Unicode),
           Column('order', Integer))

up_mappings = {'rating': 'table',
               'single_list': 'list',
               'single_select': 'select'}
down_mappings = {'table': 'rating',
                 'list': 'single_list',
                 'select': 'single_select'}


def upgrade():
    metadata.bind = op.get_bind()
    for question in op.get_bind().execute(questions.select().where(questions.c.type.in_(up_mappings.keys()))):
        qca_pk = op.get_bind().execute(qca.insert().values(question_id=question.id,
                                                           key='further',
                                                           label='Further attributes',
                                                           order=0)).inserted_primary_key
        op.get_bind().execute(qa.insert().values(question_group_id=qca_pk[0],
                                                 key='subtype',
                                                 label='Question sub-type',
                                                 value=up_mappings[question.type],
                                                 order=0))
        op.get_bind().execute(questions.update().
                              where(questions.c.id == question.id).
                              values(type='single_choice'))


def downgrade():
    metadata.bind = op.get_bind()
    for attr in op.get_bind().execute(qa.select().where(and_(qa.c.key == 'subtype',
                                                             qa.c.value.in_(down_mappings.keys())))):
        for compl_attr in op.get_bind().execute(qca.select().where(qca.c.id == attr[1])):
            op.get_bind().execute(questions.update().
                                  where(questions.c.id == compl_attr[1]).
                                  values(type=down_mappings[attr[4]]))
            op.get_bind().execute(qa.delete().where(qa.c.question_group_id == attr[1]))
            op.get_bind().execute(qca.delete().where(qca.c.id == attr[1]))
