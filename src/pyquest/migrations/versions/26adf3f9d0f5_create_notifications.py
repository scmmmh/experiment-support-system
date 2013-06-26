"""create_notifications

Revision ID: 26adf3f9d0f5
Revises: 444a8338869c
Create Date: 2013-06-21 14:15:59.605336

"""

# revision identifiers, used by Alembic.
revision = '26adf3f9d0f5'
down_revision = '6e3dd1c4643'

from alembic import op
from sqlalchemy import Column, Integer, Unicode, ForeignKey

def upgrade():
    op.create_table('notifications',
                    Column('id', Integer, primary_key=True),
                    Column('ntype', Unicode(32)),
                    Column('survey_id', Integer, ForeignKey('surveys.id', name='notifications_surveys_fk')),
                    Column('value', Integer),
                    Column('recipient', Unicode(255)),
                    Column('timestamp', Integer, default=0))

def downgrade():
    op.drop_constraint('notifications_surveys_fk', 'notifications', type='foreignkey')
    op.drop_table('notifications')
