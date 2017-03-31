"""
############################################
Migrate to the new ESS permissions structure
############################################

Revision ID: 93591ffbbc1b
Revises: 43a4951d287a
Create Date: 2017-03-30 11:43:03.609385
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '93591ffbbc1b'
down_revision = '43a4951d287a'

metadata = sa.MetaData()
permissions = sa.Table('permissions', metadata,
                       sa.Column('id', sa.Integer(), primary_key=True),
                       sa.Column('name', sa.Unicode(255)),
                       sa.Column('title', sa.Unicode(255)))
permission_groups = sa.Table('permission_groups', metadata,
                             sa.Column('id', sa.Integer(), primary_key=True),
                             sa.Column('title', sa.Unicode(255)))
permission_groups_permissions = sa.Table('permission_groups_permissions', metadata,
                                         sa.Column('permission_group_id', sa.Integer(), primary_key=True),
                                         sa.Column('permission_id', sa.Integer(), primary_key=True))
users_permission_groups = sa.Table('users_permission_groups', metadata,
                                   sa.Column('user_id', sa.Integer(), primary_key=True),
                                   sa.Column('permission_group_id', sa.Integer(), primary_key=True))
users_permissions = sa.Table('users_permissions', metadata,
                             sa.Column('user_id', sa.Integer(), primary_key=True),
                             sa.Column('permission_id', sa.Integer(), primary_key=True))

def upgrade():
    metadata.bind = op.get_bind()
    op.get_bind().execute(permissions.update().values(name='admin.users.view', title='View all users').where(permissions.c.name == 'admin.users'))
    user_view_id = op.get_bind().execute(permissions.select().where(permissions.c.name == 'admin.users.view')).first()[0]
    user_edit_id = op.get_bind().execute(permissions.insert().values(name='admin.users.edit', title='Edit all users')).inserted_primary_key[0]
    user_delete_id = op.get_bind().execute(permissions.insert().values(name='admin.users.delete', title='Delete all users')).inserted_primary_key[0]
    user_permission_id = op.get_bind().execute(permissions.insert().values(name='admin.users.permission', title="Edit all users' permissions")).inserted_primary_key[0]
    for pgp in op.get_bind().execute(permission_groups_permissions.select().where(permission_groups_permissions.c.permission_id == user_view_id)):
        op.get_bind().execute(permission_groups_permissions.insert().values(permission_group_id=pgp[0], permission_id=user_edit_id))
        op.get_bind().execute(permission_groups_permissions.insert().values(permission_group_id=pgp[0], permission_id=user_delete_id))
        op.get_bind().execute(permission_groups_permissions.insert().values(permission_group_id=pgp[0], permission_id=user_permission_id))
    for upg in op.get_bind().execute(users_permissions.select().where(users_permissions.c.permission_id == user_view_id)):
        op.get_bind().execute(users_permissions.insert().values(user_id=upg[0], permission_id=user_edit_id))
        op.get_bind().execute(users_permissions.insert().values(user_id=upg[0], permission_id=user_delete_id))
        op.get_bind().execute(users_permissions.insert().values(user_id=upg[0], permission_id=user_permission_id))
    op.get_bind().execute(permissions.update().values(name='experiment.create', title='Create new experiments').where(permissions.c.name == 'survey.new'))
    op.get_bind().execute(permissions.update().values(name='experiment.view', title='View all experiments').where(permissions.c.name == 'survey.view-all'))
    op.get_bind().execute(permissions.update().values(name='experiment.edit', title='Edit all experiments').where(permissions.c.name == 'survey.edit-all'))
    op.get_bind().execute(permissions.update().values(name='experiment.delete', title='Delete all experiments').where(permissions.c.name == 'survey.delete-all'))


def downgrade():
    metadata.bind = op.get_bind()
    op.get_bind().execute(permissions.update().values(name='admin.users', title='Administer the users').where(permissions.c.name == 'admin.users.view'))
    for permission in op.get_bind().execute(permissions.select().where(permissions.c.name.in_(['admin.users.edit', 'admin.users.delete', 'admin.users.permission']))):
        op.get_bind().execute(permission_groups_permissions.delete().where(permission_groups_permissions.c.permission_id == permission[0]))
        op.get_bind().execute(users_permissions.delete().where(users_permissions.c.permission_id == permission[0]))
        op.get_bind().execute(permissions.delete().where(permissions.c.id == permission[0]))
    op.get_bind().execute(permissions.update().values(name='survey.new', title='Create new surveys').where(permissions.c.name == 'experiment.create'))
    op.get_bind().execute(permissions.update().values(name='survey.view-all', title='View all surveys').where(permissions.c.name == 'experiment.view'))
    op.get_bind().execute(permissions.update().values(name='survey.edit-all', title='Edit all surveys').where(permissions.c.name == 'experiment.edit'))
    op.get_bind().execute(permissions.update().values(name='survey.delete-all', title='Delete all surveys').where(permissions.c.name == 'experiment.delete'))
