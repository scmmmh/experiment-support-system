"""Simplify Transitions

Revision ID: 4c876b48f28b
Revises: 44a76d75263
Create Date: 2013-09-13 14:43:54.858953

"""

# revision identifiers, used by Alembic.
revision = '4c876b48f28b'
down_revision = '44a76d75263'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('qsheet_transitions', sa.Column('order', sa.Integer, default=0))
    op.add_column('qsheet_transitions', sa.Column('_condition', sa.UnicodeText))
    op.add_column('qsheet_transitions', sa.Column('_action', sa.UnicodeText))
    op.drop_table('transition_conditions')
    
def downgrade():
    op.drop_column('qsheet_transitions', '_action')
    op.drop_column('qsheet_transitions', '_condition')
    op.drop_column('qsheet_transitions', 'order')
    op.create_table('transition_conditions',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('expected_answer', sa.VARCHAR(255)),
                    sa.Column('transition_id', sa.Integer, sa.ForeignKey('qsheet_transitions.id', name='transition_conditions_qsheet_transitions_fk')),
                    sa.Column('question_id', sa.Integer, sa.ForeignKey('questions.id')),
                    sa.Column('subquestion_name', sa.VARCHAR(255)))
