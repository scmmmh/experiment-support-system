"""
##################
Fix question types
##################

Revision ID: 315f2a8005ca
Revises: 1cd78b756fb3
Create Date: 2013-06-05 11:08:43.563406
"""
import re
from alembic import op
from sqlalchemy import Table, MetaData, Column, Integer, Unicode


# revision identifiers, used by Alembic.
revision = '315f2a8005ca'
down_revision = '1cd78b756fb3'

questions = Table('questions', MetaData(),
                  Column('id', Integer, primary_key=True),
                  Column('name', Unicode))


def upgrade():
    for question in op.get_bind().execute(questions.select()):
        name = str(question.name)
        new_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        if new_name != name:
            op.get_bind().execute(questions.update().where(questions.c.id == question.id).values(name=new_name))


# Nothing can be done to reverse this change
def downgrade():
    pass
