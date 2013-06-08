"""Enable QuestionType and QuestionTypeGroup administration

Revision ID: 305eb54c5d1c
Revises: 26421c11f65d
Create Date: 2013-04-21 17:09:58.743750

"""

# revision identifiers, used by Alembic.
revision = '305eb54c5d1c'
down_revision = '26421c11f65d'

from alembic import op
import sqlalchemy as sa

metadata = sa.MetaData()

perm = sa.Table('permissions', metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('name', sa.Unicode(255), index=True, unique=True),
                sa.Column('title', sa.Unicode(255)))

qt = sa.Table('question_types', metadata,
              sa.Column('enabled', sa.Boolean))

qtg = sa.Table('question_type_groups', metadata,
               sa.Column('enabled', sa.Boolean))

def upgrade():
    metadata.bind = op.get_bind()
    op.get_bind().execute(perm.insert(values={u'name': u'admin.question_types', u'title': u'Administer the question types'}))
    op.add_column('question_types', sa.Column('enabled', sa.Boolean))
    op.add_column('question_types', sa.Column('order', sa.Integer))
    op.get_bind().execute(qt.update(values={u'enabled': True}))
    op.add_column('question_type_groups', sa.Column('enabled', sa.Boolean))
    op.get_bind().execute(qtg.update(values={u'enabled': True}))


def downgrade():
    op.get_bind().execute(perm.delete(perm.c.name==u'admin.question_types'))
    op.drop_column('question_types', 'enabled')
    op.drop_column('question_types', 'order')
    op.drop_column('question_type_groups', 'enabled')
    