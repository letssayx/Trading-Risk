"""add_agm_events

Revision ID: 20260804_191457
Revises: fix_mto_bigint_001_fix_overflow
Create Date: 2026-08-04T19:14:57.533936

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260804_191457'
down_revision: Union[str, None] = 'fix_mto_bigint_001_fix_overflow'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('agm_events',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('symbol', sa.String(length=50), nullable=False),
    sa.Column('company_name', sa.String(length=200), nullable=True),
    sa.Column('agm_announcement_date', sa.Date(), nullable=True),
    sa.Column('agm_date', sa.Date(), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'agm_announcement_date', 'agm_date', name='uq_agm_event_unique')
    )
    op.create_index(op.f('ix_agm_events_date'), 'agm_events', ['date'], unique=False)
    op.create_index(op.f('ix_agm_events_symbol'), 'agm_events', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agm_events_symbol'), table_name='agm_events')
    op.drop_index(op.f('ix_agm_events_date'), table_name='agm_events')
    op.drop_table('agm_events')
