"""
#######################
Create User Preferences
#######################

Revision ID: 105647470980
Revises: 1341b5a7b155
Create Date: 2012-10-06 12:01:44.553261
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '105647470980'
down_revision = '1341b5a7b155'

metadata = sa.MetaData()

ut = sa.Table('users', metadata,
              sa.Column('id', sa.Integer, primary_key=True))


def upgrade():
    metadata.bind = op.get_bind()
    op.create_table('user_preferences',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('user_id', sa.Integer,
                              sa.ForeignKey('users.id', name='user_preferences_users_fk'), index=True),
                    sa.Column('key', sa.Unicode(255)),
                    sa.Column('value', sa.Unicode(255)))


def downgrade():
    op.drop_constraint('user_preferences_users_fk', 'user_preferences', type='foreignkey')
    op.drop_table('user_preferences')
