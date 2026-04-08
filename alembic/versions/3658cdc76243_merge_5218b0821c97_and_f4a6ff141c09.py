"""Merge 5218b0821c97 and f4a6ff141c09

Revision ID: 3658cdc76243
Revises: 5218b0821c97, f4a6ff141c09
Create Date: 2026-04-08 19:56:26.645690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3658cdc76243'
down_revision: Union[str, Sequence[str], None] = ('5218b0821c97', 'f4a6ff141c09')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
