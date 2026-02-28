"""clear empty success logs

Revision ID: fix_empty_success_logs_005
Revises: fix_mwpl_logs_004
Create Date: 2026-02-28 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'fix_empty_success_logs_005'
down_revision = 'fix_mwpl_logs_004'
branch_labels = None
depends_on = None

def upgrade():
    # Remove all "SUCCESS" records where no rows were inserted
    # This specifically targets the MWPL bug that recorded a success for an empty parse
    # By deleting them, the system will re-fetch the data on the next import run
    conn = op.get_bind()
    conn.execute(
        text("DELETE FROM import_logs WHERE status = 'SUCCESS' AND (rows_inserted = 0 OR rows_inserted IS NULL) AND table_name != 'auctions'")
    )

def downgrade():
    pass
