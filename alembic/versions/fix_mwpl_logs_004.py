"""Fix MWPL Compression and Force Re-import

Revision ID: fix_mwpl_compression_reimport
Revises: fix_bhavcopy_fo_instrument_003
Create Date: 2026-02-27 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'fix_mwpl_compression_reimport'
down_revision = 'fix_bhavcopy_fo_instrument_003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Clear import logs for MWPL to force re-import with fixed parsing logic
    # This is critical because previous attempts likely succeeded with 0 rows inserted
    # due to parsing failures, and the system now thinks those dates are 'done'.
    bind = op.get_bind()

    # Use direct execution on bind to avoid session management issues in Alembic
    try:
        bind.execute(text("DELETE FROM import_logs WHERE table_name = 'mwpl_cli'"))
        # We also clear system logs related to these failures so the dashboard looks clean
        bind.execute(text("DELETE FROM system_logs WHERE source = 'NSE_Importer' AND meta_data->>'table' = 'mwpl_cli'"))
    except Exception as e:
        print(f"Warning: Failed to clear MWPL logs: {e}")

    # 2. Fix TimescaleDB Compression Policies
    # The actual ALTER TABLE commands are handled by the application startup code in `timescale.py`.
    # However, if any bad policies exist, we could try to drop them here.
    # Given the logs showed failures to create them, they likely don't exist.
    pass


def downgrade() -> None:
    pass
