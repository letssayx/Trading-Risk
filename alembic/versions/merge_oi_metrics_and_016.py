"""Merge OI metrics and 016

Revision ID: merge_oi_and_016
Revises: 016_bhavcopy_fo_duplicates_fix, create_oi_analysis_metrics
Create Date: 2024-05-01 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_oi_and_016'
down_revision = ('016_bhavcopy_fo_duplicates_fix', 'create_oi_analysis_metrics')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
