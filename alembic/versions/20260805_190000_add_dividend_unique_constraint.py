"""add_dividend_unique_constraint

Revision ID: 20260805_190000
Revises:
Create Date: 2026-08-05 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260805_190000'
down_revision = '20260714072610'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First deduplicate existing rows that might violate the new constraint
    op.execute('''
        DELETE FROM dividend_databank
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER(
                    PARTITION BY symbol, date, dividend_type
                    ORDER BY id DESC
                ) as row_num
                FROM dividend_databank
            ) t
            WHERE t.row_num > 1
        )
    ''')

    op.create_unique_constraint(
        'uq_dividend_databank_unique',
        'dividend_databank',
        ['symbol', 'date', 'dividend_type']
    )


def downgrade() -> None:
    op.drop_constraint('uq_dividend_databank_unique', 'dividend_databank', type_='unique')
