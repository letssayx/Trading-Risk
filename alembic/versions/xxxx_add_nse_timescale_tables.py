"""Add NSE Tables with TimescaleDB Support

Revision ID: nse_timescale_v1
Revises: previous_migration_id
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Tables are created via SQLAlchemy models
    # TimescaleDB policies are applied via setup_timescale_policies() task
    # Run this after migration: celery -A backend.tasks call backend.ingest.tasks.setup_timescale_policies
    pass

def downgrade():
    # TimescaleDB hypertables cannot be easily downgraded
    pass
