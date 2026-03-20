from alembic import op
import sqlalchemy as sa

revision = '015_add_broadcast_dates'
down_revision = '014_parsed_dividend'
branch_labels = None
depends_on = None

def upgrade():
    # board_meetings
    op.add_column('board_meetings', sa.Column('broadcast_date', sa.DateTime(), nullable=True))
    op.add_column('board_meetings', sa.Column('meeting_date', sa.Date(), nullable=True))

    # corporate_actions
    op.add_column('corporate_actions', sa.Column('broadcast_date', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('corporate_actions', 'broadcast_date')
    op.drop_column('board_meetings', 'meeting_date')
    op.drop_column('board_meetings', 'broadcast_date')
