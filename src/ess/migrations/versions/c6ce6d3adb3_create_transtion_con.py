"""
############################
Create transition conditions
############################

Revision ID: c6ce6d3adb3
Revises: 33d37cab0f8a
Create Date: 2013-05-02 17:07:15.913485

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c6ce6d3adb3'
down_revision = '305eb54c5d1c'


def upgrade():
    op.create_table('transition_conditions',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('expected_answer', sa.VARCHAR(255)),
                    sa.Column('transition_id',
                              sa.Integer,
                              sa.ForeignKey('qsheet_transitions.id',
                                            name='transition_conditions_qsheet_transitions_fk')),
                    sa.Column('question_id', sa.Integer, sa.ForeignKey('questions.id')),
                    sa.Column('subquestion_name', sa.VARCHAR(255)))


def downgrade():
    op.drop_table('transition_conditions')
