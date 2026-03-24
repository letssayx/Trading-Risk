"""Fix bhavcopy_fo unique constraint and duplicate handling

Revision ID: 016_bhavcopy_fo_duplicates_fix
Revises: 015_add_broadcast_dates
Create Date: 2026-03-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '016_bhavcopy_fo_duplicates_fix'
down_revision = '015_add_broadcast_dates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    constraints = inspector.get_unique_constraints('bhavcopy_fo')
    constraint_names = [c['name'] for c in constraints]

    # If the unique constraint already exists, it may be the old one. We recreate it safely.
    if 'uq_bhavcopy_fo_unique' in constraint_names:
        op.drop_constraint('uq_bhavcopy_fo_unique', 'bhavcopy_fo', type_='unique')

    # Remove duplicates before adding unique constraint
    op.execute("""
    DELETE FROM bhavcopy_fo a USING (
      SELECT MIN(id) as id, trade_date, ticker_symb, instrument_type, expiry_date, strike_price, option_type
      FROM bhavcopy_fo
      GROUP BY trade_date, ticker_symb, instrument_type, expiry_date, strike_price, option_type HAVING COUNT(*) > 1
    ) b
    WHERE a.trade_date = b.trade_date
      AND a.ticker_symb = b.ticker_symb
      AND a.instrument_type = b.instrument_type
      AND a.expiry_date = b.expiry_date
      AND a.strike_price = b.strike_price
      AND a.option_type = b.option_type
      AND a.id > b.id;
    """)

    op.create_unique_constraint(
        'uq_bhavcopy_fo_unique',
        'bhavcopy_fo',
        ['trade_date', 'ticker_symb', 'instrument_type', 'expiry_date', 'strike_price', 'option_type']
    )


def downgrade() -> None:
    op.drop_constraint('uq_bhavcopy_fo_unique', 'bhavcopy_fo', type_='unique')
    op.create_unique_constraint(
        'uq_bhavcopy_fo_unique',
        'bhavcopy_fo',
        ['trade_date', 'ticker_symb', 'expiry_date', 'strike_price', 'option_type']
    )
