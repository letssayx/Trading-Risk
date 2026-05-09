"""merge_016_and_5218b

Revision ID: aa349ce81712
Revises: b6f693c0aeff, 5218b0821c97
Create Date: 2026-05-09 09:54:19.164821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa349ce81712'
down_revision: Union[str, Sequence[str], None] = ('b6f693c0aeff', '5218b0821c97')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
