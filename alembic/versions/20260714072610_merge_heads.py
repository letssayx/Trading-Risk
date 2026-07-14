"""Merge heads

Revision ID: 20260714072610
Revises: 018_fix_corp_actions, 20260714062540
Create Date: 2026-07-14T07:26:10.463954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260714072610'
down_revision = ('018_fix_corp_actions', '20260714062540')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
