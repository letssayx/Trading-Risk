"""merge_heads

Revision ID: b110b082b694
Revises: b6f693c0aeff, 5218b0821c97
Create Date: 2026-06-28 21:02:41.355299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b110b082b694'
down_revision: Union[str, Sequence[str], None] = ('b6f693c0aeff', '5218b0821c97')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
