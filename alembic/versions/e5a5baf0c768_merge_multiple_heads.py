"""merge multiple heads

Revision ID: e5a5baf0c768
Revises: 20260714072610, add_needs_review_audit_flag
Create Date: 2026-08-23 19:31:01.097291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a5baf0c768'
down_revision: Union[str, Sequence[str], None] = ('20260714072610', 'add_needs_review_audit_flag')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
