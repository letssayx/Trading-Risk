"""add vwap column

Revision ID: 012_add_vwap
Revises: 440393f5b569
Create Date: 2026-03-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012_add_vwap'
down_revision = '440393f5b569'
branch_labels = None
depends_on = None

def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'vwap' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('vwap', sa.Float(), nullable=True))


def downgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'vwap' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'vwap')