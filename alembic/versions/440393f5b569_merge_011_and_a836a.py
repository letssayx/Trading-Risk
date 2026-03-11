"""merge_011_and_a836a

Revision ID: 440393f5b569
Revises: a836a8ddcd34, 011_mr_metrics
Create Date: 2026-03-11 08:34:09.208953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '440393f5b569'
down_revision: Union[str, Sequence[str], None] = ('a836a8ddcd34', '011_mr_metrics')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
