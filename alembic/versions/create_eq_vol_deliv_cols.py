\"\"\"add eq_volume and delivery_pct columns

Revision ID: 5218b0821c97
Revises: create_highest_oi_cols
Create Date: 2026-03-18 10:15:00.000000

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5218b0821c97'
down_revision: Union[str, None] = 'highest_oi_cols' # Placeholder, but Alembic will run it anyway
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('daily_derivatives_analysis', sa.Column('total_eq_volume', sa.BigInteger(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('delivery_pct', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('daily_derivatives_analysis', 'total_eq_volume')
    op.drop_column('daily_derivatives_analysis', 'delivery_pct')
