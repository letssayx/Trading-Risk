"""Fix corporate_actions and board_meetings unique constraints

Revision ID: 018_fix_corp_actions_bm_constraints
Revises: 017_add_uq_historical_atm_iv_unique
Create Date: 2026-07-05 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '018_fix_corp_actions'
down_revision = '017_uq_atm_iv'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check board_meetings
    if 'board_meetings' in inspector.get_table_names():
        constraints = inspector.get_unique_constraints('board_meetings')
        constraint_names = [c['name'] for c in constraints]

        if 'uq_board_meeting_unique' not in constraint_names:
            op.create_unique_constraint('uq_board_meeting_unique', 'board_meetings', ['date', 'symbol', 'purpose'])

    # Check corporate_actions
    if 'corporate_actions' in inspector.get_table_names():
        constraints = inspector.get_unique_constraints('corporate_actions')
        constraint_names = [c['name'] for c in constraints]

        if 'uq_corp_action_unique' not in constraint_names:
            op.create_unique_constraint('uq_corp_action_unique', 'corporate_actions', ['date', 'symbol', 'purpose'])

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if 'board_meetings' in inspector.get_table_names():
        constraints = inspector.get_unique_constraints('board_meetings')
        if 'uq_board_meeting_unique' in [c['name'] for c in constraints]:
            op.drop_constraint('uq_board_meeting_unique', 'board_meetings', type_='unique')

    if 'corporate_actions' in inspector.get_table_names():
        constraints = inspector.get_unique_constraints('corporate_actions')
        if 'uq_corp_action_unique' in [c['name'] for c in constraints]:
            op.drop_constraint('uq_corp_action_unique', 'corporate_actions', type_='unique')
