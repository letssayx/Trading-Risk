"""Merge 5218b0821c97 and f4a6ff141c09

Revision ID: 28f29aaf0c55
Revises: 5218b0821c97, f4a6ff141c09
Create Date: 2026-04-08 19:38:03.082707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28f29aaf0c55'
down_revision: Union[str, Sequence[str], None] = ('5218b0821c97', 'f4a6ff141c09')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
