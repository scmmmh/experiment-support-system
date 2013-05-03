"""Improve QuestionType structuring

Revision ID: 26421c11f65d
Revises: 64ef6deb982
Create Date: 2013-04-21 15:21:29.230390

"""

# revision identifiers, used by Alembic.
revision = '26421c11f65d'
down_revision = '64ef6deb982'

from alembic import op
import sqlalchemy as sa

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
                  sa.Column('parent_id', sa.Integer, sa.ForeignKey('question_type_groups.id', name='question_type_groups_parent_fk')))
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name==u'core')).first()[0]
    qtg_pk = op.get_bind().execute(qtg.insert().values(name=u'text', title=u'Text', order=0, parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id==qtg_id, qt.c.name.in_([u'text', u'short_text', u'long_text', u'number', u'email', u'url', u'date', u'time', u'datetime', u'month']))).values({'group_id': qtg_pk}))
    qtg_pk = op.get_bind().execute(qtg.insert().values(name=u'choice', title=u'Choice', order=1, parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id==qtg_id, qt.c.name.in_([u'single_choice', u'multi_choice', u'single_choice_grid', u'multi_choice_grid', u'country', u'language']))).values({'group_id': qtg_pk}))
    qtg_pk = op.get_bind().execute(qtg.insert().values(name=u'hidden', title=u'Hidden', order=2, parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id==qtg_id, qt.c.name.in_([u'page_timer', u'hidden_value', u'auto_commit']))).values({'group_id': qtg_pk}))
    qtg_pk = op.get_bind().execute(qtg.insert().values(name=u'other', title=u'Other', order=3, parent_id=qtg_id)).inserted_primary_key[0]
    op.get_bind().execute(qt.update().where(sa.and_(qt.c.group_id==qtg_id, qt.c.name.in_([u'confirm', u'ranking', u'js_check']))).values({'group_id': qtg_pk}))


def downgrade():
    metadata.bind = op.get_bind()
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name==u'core')).first()[0]
    op.get_bind().execute(qt.update().where(qt.c.group_id.in_(sa.select([qtg.c.id]).where(qtg.c.parent_id==qtg_id))).values({'group_id': qtg_id}))
    op.get_bind().execute(qtg.delete().where(qtg.c.parent_id==qtg_id))
    op.drop_constraint('question_type_groups_parent_fk', 'question_type_groups', type='foreignkey')
    op.drop_column('question_type_groups', 'parent_id')
