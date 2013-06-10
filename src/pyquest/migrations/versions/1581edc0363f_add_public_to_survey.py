"""add_public_to_survey

Revision ID: 1581edc0363f
Revises: 315f2a8005ca
Create Date: 2013-06-07 19:06:44.932664

"""

# revision identifiers, used by Alembic.
revision = '1581edc0363f'
down_revision = '17c68d338ee4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('surveys', sa.Column('public', sa.Boolean(), default=True))

    surveys = sa.Table('surveys', sa.MetaData(),
           sa.Column('id', sa.Integer, primary_key=True),
           sa.Column('public', sa.Boolean))
    
    for survey in op.get_bind().execute(surveys.select()):
        op.get_bind().execute(surveys.update().where(surveys.c.id==survey.id).values(public='1'))

def downgrade():
    op.drop_column('surveys', 'public')

