"""Create User Preferences

Revision ID: 105647470980
Revises: 1341b5a7b155
Create Date: 2012-10-06 12:01:44.553261

"""

# revision identifiers, used by Alembic.
revision = '105647470980'
down_revision = '1341b5a7b155'

from alembic import op
import sqlalchemy as sa

metadata = sa.MetaData()

ut = sa.Table('users', metadata,
              sa.Column('id', sa.Integer, primary_key=True))

def upgrade():
    metadata.bind = op.get_bind()
    op.create_table('user_preferences',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
                    sa.Column('key', sa.Unicode()),
                    sa.Column('value', sa.Unicode()))


def downgrade():
    op.drop_table('user_preferences')
