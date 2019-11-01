"""
#######################
Fix page timer question
#######################

Revision ID: 43ad0a13e1ea
Revises: 319a0b5f9c3d
Create Date: 2013-03-10 19:16:32.324272
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43ad0a13e1ea'
down_revision = '319a0b5f9c3d'

metadata = sa.MetaData()
qtg = sa.Table('question_type_groups', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.Unicode(255)))
qt = sa.Table('question_types', metadata,
              sa.Column('group_id', sa.Integer),
              sa.Column('name', sa.Unicode(255)),
              sa.Column('backend', sa.UnicodeText),
              sa.Column('frontend', sa.UnicodeText))


def upgrade():
    metadata.bind = op.get_bind()
    core_qtg = op.get_bind().execute(qtg.select(qtg.c.name == 'core')).first()
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'page_timer'),
                                    {'frontend': """${f.hidden_field(name, '0', class_='role-timer')}"""}))
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'auto_commit'),
                                    {'frontend': """<script type="text/javascript">$(document).ready(function() {setTimeout(function() {var frm = $('form.role-survey-form'); frm.append('<input type="hidden" name="action_" value="Next Page"/>'); frm.submit();}, ${q.attr_value('further.timeout') * 1000})});</script>"""}))  # noqa


def downgrade():
    metadata.bind = op.get_bind()
    core_qtg = op.get_bind().execute(qtg.select(qtg.c.name == 'core')).first()
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'page_timer'),
                                    {'frontend': """<script type="text/javascript">$(document).ready(function() {setTimeout(function() {var frm = $('form.role-survey-form'); frm.append('<input type="hidden" name="action_" value="Next Page"/>'); frm.submit();}, ${q.attr_value('further.timeout') * 1000})});</script>"""}))  # noqa
    op.get_bind().execute(qt.update(sa.and_(qt.c.group_id == core_qtg[0], qt.c.name == 'auto_commit'),
                                    {'frontend': """${f.hidden_field(name, '0', None, class_='role-timer')}"""}))
