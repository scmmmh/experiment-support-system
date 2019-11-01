"""
################################
Improve QuestionType structuring
################################

Revision ID: 26421c11f65d
Revises: 64ef6deb982
Create Date: 2013-04-21 15:21:29.230390
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26421c11f65d'
down_revision = '64ef6deb982'

metadata = sa.MetaData()
qt = sa.Table('question_types', metadata,
              sa.Column('id', sa.Integer, primary_key=True),
              sa.Column('name', sa.Unicode(255)),
              sa.Column('group_id', sa.Unicode(255)))
qtg = sa.Table('question_type_groups', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.Unicode(255), unique=True),
               sa.Column('title', sa.Unicode(255)),
               sa.Column('order', sa.Integer),
               sa.Column('parent_id', sa.Integer))


def upgrade():
    metadata.bind = op.get_bind()
    op.add_column('question_type_groups',
                  sa.Column('parent_id', sa.Integer, sa.ForeignKey('question_type_groups.id',
                                                                   name='question_type_groups_parent_fk')))
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name == 'core')).first()[0]
    qtg_pk = op.get_bind().execute(qtg.insert().values(name='text',
                                                       title='Text',
                                                       order=0,
                                                       parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id == qtg_id,
                                                    qt.c.name.in_(['text', 'short_text', 'long_text', 'number',
                                                                   'email', 'url', 'date', 'time', 'datetime',
                                                                   'month']))).values({'group_id': qtg_pk}))
    qtg_pk = op.get_bind().execute(qtg.insert().values(name='choice',
                                                       title='Choice',
                                                       order=1,
                                                       parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id == qtg_id,
                                                    qt.c.name.in_(['single_choice', 'multi_choice',
                                                                   'single_choice_grid', 'multi_choice_grid',
                                                                   'country', 'language']))).
                          values({'group_id': qtg_pk}))
    qtg_pk = op.get_bind().execute(qtg.insert().values(name='hidden',
                                                       title='Hidden',
                                                       order=2,
                                                       parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id == qtg_id,
                                                    qt.c.name.in_(['page_timer', 'hidden_value', 'auto_commit']))).
                          values({'group_id': qtg_pk}))
    qtg_pk = op.get_bind().execute(qtg.insert().values(name='other',
                                                       title='Other',
                                                       order=3,
                                                       parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id == qtg_id,
                                                    qt.c.name.in_(['confirm', 'ranking', 'js_check']))).
                          values({'group_id': qtg_pk}))


def downgrade():
    metadata.bind = op.get_bind()
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name == 'core')).first()[0]
    op.get_bind().execute(qt.update().where(qt.c.group_id.in_(sa.select([qtg.c.id]).
                                                              where(qtg.c.parent_id == qtg_id))).
                          values({'group_id': qtg_id}))
    op.get_bind().execute(qtg.delete().where(qtg.c.parent_id == qtg_id))
    op.drop_constraint('question_type_groups_parent_fk', 'question_type_groups', type='foreignkey')
    op.drop_column('question_type_groups', 'parent_id')
