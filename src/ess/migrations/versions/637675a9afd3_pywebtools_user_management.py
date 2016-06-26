"""
##########################
PyWebTools user management
##########################

Update the user and permission management tables for use with PyWebTools

Revision ID: 637675a9afd3
Revises: 5a464c95c7f1
Create Date: 2016-06-25 17:02:57.417587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '637675a9afd3'
down_revision = '5a464c95c7f1'

metadata = sa.MetaData()
users = sa.Table('users', metadata,
                 sa.Column('status', sa.Unicode(255)))
gp_old = sa.Table('groups_permissions', metadata,
                  sa.Column('group_id', sa.Integer()),
                  sa.Column('permission_id', sa.Integer()))
gp_new = sa.Table('permission_groups_permissions', metadata,
                  sa.Column('permission_group_id', sa.Integer()),
                  sa.Column('permission_id', sa.Integer()))
ug_old = sa.Table('users_groups', metadata,
                  sa.Column('user_id', sa.Integer()),
                  sa.Column('group_id', sa.Integer()))
ug_new = sa.Table('users_permission_groups', metadata,
                  sa.Column('user_id', sa.Integer()),
                  sa.Column('permission_group_id', sa.Integer()))


def upgrade():
    bind = op.get_bind()
    metadata.bind = bind
    # Fix the users table
    op.drop_column('users', 'username')
    op.create_unique_constraint('users_username_uq', 'users', ['email'])
    op.add_column('users', sa.Column('status', sa.Unicode(255)))
    bind.execute(users.update().values(status='active'))
    # Rename the permission_groups table
    op.rename_table('groups', 'permission_groups')
    # Replate the groups_permissions with permission_groups_permissions table
    op.create_table('permission_groups_permissions',
                    sa.Column('permission_group_id',
                              sa.Integer,
                              sa.ForeignKey('permission_groups.id', name='permission_groups_permissions_groups_fk'),
                              primary_key=True),
                    sa.Column('permission_id',
                              sa.Integer,
                              sa.ForeignKey('permissions.id', name='permission_groups_permissions_permissions_fk'),
                              primary_key=True))
    bind.execute(gp_new.insert().from_select(['permission_group_id', 'permission_id'], gp_old.select()))
    op.drop_table('groups_permissions')
    # Replace the users_groups with users_permission_groups table
    op.create_table('users_permission_groups',
                    sa.Column('user_id',
                              sa.Integer,
                              sa.ForeignKey('users.id', name='users_permission_groups_users_fk'),
                              primary_key=True),
                    sa.Column('permission_group_id',
                              sa.Integer,
                              sa.ForeignKey('permission_groups.id', name='users_permission_groups_groups_fk'),
                              primary_key=True))
    bind.execute(ug_new.insert().from_select(['user_id', 'permission_group_id'], ug_old.select()))
    op.drop_table('users_groups')
    # Add time_tokens table
    op.create_table('time_tokens',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id',
                                                                   name='time_tokens_user_id_fk')),
                    sa.Column('action', sa.Unicode(255)),
                    sa.Column('token', sa.Unicode(255)),
                    sa.Column('timeout', sa.DateTime()),
                    sa.Column('data', sa.UnicodeText()))
    op.create_index('time_tokens_full_ix', 'time_tokens',
                    ['action', 'token', 'timeout'])


def downgrade():
    bind = op.get_bind()
    metadata.bind = bind
    # Revert the users table
    op.add_column('users', sa.Column('username', sa.Unicode(255), unique=True, index=True))
    op.drop_constraint('users_username_uq', 'users')
    op.drop_column('users', 'status')
    # Revert the groups_permissions with permission_groups_permissions table change
    op.create_table('groups_permissions',
                    sa.Column('group_id',
                              sa.Integer,
                              sa.ForeignKey('permission_groups.id', name='groups_permissions_groups_fk'),
                              primary_key=True),
                    sa.Column('permission_id',
                              sa.Integer,
                              sa.ForeignKey('permissions.id', name='groups_permissions_permissions_fk'),
                              primary_key=True))
    bind.execute(gp_old.insert().from_select(['group_id', 'permission_id'], gp_new.select()))
    op.drop_table('permission_groups_permissions')
    # Revert the users_groups with users_permission_groups table change
    op.create_table('users_groups',
                    sa.Column('user_id',
                              sa.Integer,
                              sa.ForeignKey('users.id', name='users_groups_users_fk'),
                              primary_key=True),
                    sa.Column('group_id',
                              sa.Integer,
                              sa.ForeignKey('permission_groups.id', name='users_groups_groups_fk'),
                              primary_key=True))
    bind.execute(ug_old.insert().from_select(['user_id', 'group_id'], ug_new.select()))
    op.drop_table('users_permission_groups')
    # Revert the permission_groups table to groups
    op.rename_table('permission_groups', 'groups')
    # Remove time_tokens table
    op.drop_table('time_tokens')
