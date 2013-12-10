"""Add explicit participant completed flag

Revision ID: 5008e04b83bb
Revises: 4c876b48f28b
Create Date: 2013-12-10 19:54:12.582936

"""

# revision identifiers, used by Alembic.
revision = '5008e04b83bb'
down_revision = '4c876b48f28b'

from alembic import op
import sqlalchemy as sa

metadata = sa.MetaData()

participants = sa.Table('participants', metadata,
                        sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('completed', sa.Boolean()),
                        sa.Column('survey_id', sa.Integer))
qsheets = sa.Table('qsheets', metadata,
                   sa.Column('id', sa.Integer, primary_key=True),
                   sa.Column('survey_id', sa.Integer))
questions = sa.Table('questions', metadata,
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('qsheet_id', sa.Integer),
                     sa.Column('required', sa.Boolean))
answers = sa.Table('answers', metadata,
                   sa.Column('id', sa.Integer, primary_key=True),
                   sa.Column('question_id', sa.Integer),
                   sa.Column('participant_id', sa.Integer))
def upgrade():
    metadata.bind = op.get_bind()
    op.add_column('participants', sa.Column('completed', sa.Boolean, default=False))
    for participant in op.get_bind().execute(participants.select()):
        completed = True
        for question in op.get_bind().execute(questions.select().select_from(questions.join(qsheets, questions.c.qsheet_id==qsheets.c.id)).where(qsheets.c.survey_id==participant.survey_id)):
            if question.required:
                if not op.get_bind().execute(answers.select().where(sa.and_(answers.c.participant_id==participant.id, answers.c.question_id==question.id))).first():
                    completed = False
        op.get_bind().execute(participants.update().values(completed=completed).where(participants.c.id==participant.id))

def downgrade():
    op.drop_column('participants', 'completed')
