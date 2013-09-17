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
import json

metadata = sa.MetaData()

qs = sa.Table('qsheets', metadata,
              sa.Column('id', sa.Integer, primary_key=True),
              sa.Column('name', sa.Unicode))

q = sa.Table('questions', metadata,
             sa.Column('id', sa.Integer, primary_key=True),
             sa.Column('qsheet_id', sa.Integer),
             sa.Column('name', sa.Unicode))

qt = sa.Table('qsheet_transitions', metadata,
              sa.Column('id', sa.Integer, primary_key=True),
              sa.Column('source_id', sa.Integer, sa.ForeignKey('qsheets.id', name='qsheet_transitions_qsheets_source_fk')),
              sa.Column('target_id', sa.Integer, sa.ForeignKey('qsheets.id', name='qsheet_transitions_qsheets_target_fk')),
              sa.Column('order', sa.Integer, default=0),
              sa.Column('_condition', sa.UnicodeText))

tc = sa.Table('transition_conditions', metadata,
              sa.Column('id', sa.Integer, primary_key=True),
              sa.Column('expected_answer', sa.VARCHAR(255)),
              sa.Column('transition_id', sa.Integer, sa.ForeignKey('qsheet_transitions.id', name='transition_conditions_qsheet_transitions_fk')),
              sa.Column('question_id', sa.Integer, sa.ForeignKey('questions.id')),
              sa.Column('subquestion_name', sa.VARCHAR(255)))

def upgrade():
    op.add_column('qsheet_transitions', sa.Column('order', sa.Integer, default=0))
    op.add_column('qsheet_transitions', sa.Column('_condition', sa.UnicodeText))
    op.add_column('qsheet_transitions', sa.Column('_action', sa.UnicodeText))
    for row in op.get_bind().execute(sa.select([tc.c.expected_answer, qt.c.id, q.c.name, qs.c.name], sa.and_(qt.c.id==tc.c.transition_id,
                                                                                                             tc.c.question_id==q.c.id,
                                                                                                             q.c.qsheet_id==qs.c.id))):
        data = {'type': 'answer',
                'question': '%s.%s' % (row[3], row[2]),
                'answer': row[0]}
        op.get_bind().execute(qt.update().where(qt.c.id==row[1]).values(_condition=json.dumps(data)))
    op.drop_table('transition_conditions')
    
def downgrade():
    op.create_table('transition_conditions',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('expected_answer', sa.VARCHAR(255)),
                    sa.Column('transition_id', sa.Integer, sa.ForeignKey('qsheet_transitions.id', name='transition_conditions_qsheet_transitions_fk')),
                    sa.Column('question_id', sa.Integer, sa.ForeignKey('questions.id')),
                    sa.Column('subquestion_name', sa.VARCHAR(255)))
    for row in op.get_bind().execute(qt.select().where(qt.c._condition!=None)):
        data = json.loads(row[4])
        if data['type'] == 'answer':
            qs_name, q_name = data['question'].split('.')
            quest = op.get_bind().execute(sa.select([q], sa.and_(q.c.name==q_name,
                                                                 q.c.qsheet_id==qs.c.id,
                                                                 qs.c.name==qs_name))).first()
            if quest:
                op.get_bind().execute(tc.insert().values(transition_id=row[0],
                                                         expected_answer=data['answer'],
                                                         question_id=quest[0]))
    op.drop_column('qsheet_transitions', '_action')
    op.drop_column('qsheet_transitions', '_condition')
    op.drop_column('qsheet_transitions', 'order')
