"""Fix hidden field rendering

Revision ID: 11b7c2763658
Revises: 6a2436d1eed
Create Date: 2014-07-09 10:48:44.031593

"""

# revision identifiers, used by Alembic.
revision = '11b7c2763658'
down_revision = '6a2436d1eed'

from alembic import op
import sqlalchemy as sa

metadata = sa.MetaData()

qt = sa.Table('question_types', metadata,
              sa.Column('id', sa.Integer),
              sa.Column('name', sa.Unicode(255)),
              sa.Column('frontend', sa.UnicodeText),
              sa.Column('group_id', sa.Integer))

qtg = sa.Table('question_type_groups', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.Unicode(255), unique=True),
               sa.Column('parent_id', sa.Integer))

def upgrade():
    metadata.bind = op.get_bind()
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name==u'core')).first()[0]
    qtg_id = op.get_bind().execute(qtg.select().where(sa.and_(qtg.c.parent_id == qtg_id,
                                                              qtg.c.name==u'hidden'))).first()[0]
    op.get_bind().execute(qt.update().\
                          where(sa.and_(qt.c.group_id == qtg_id, qt.c.name == u'hidden_value')).\
                          values({'frontend': u"${f.hidden_field(name, sub(q.attr_value('further.value'), i, p))}"}))


def downgrade():
    metadata.bind = op.get_bind()
    qtg_id = op.get_bind().execute(qtg.select().where(qtg.c.name==u'core')).first()[0]
    op.get_bind().execute(qt.update().\
                          where(sa.and_(qt.c.group_id == qtg_id, qt.c.name == u'hidden_value')).\
                          values({'frontend': u"${f.hidden_field(name, sub(q.attr_value('further.value'), i, p), None)}"}))
