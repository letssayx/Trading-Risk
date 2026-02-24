"""Add NSE TimescaleDB models

Revision ID: ea79cf6bfcdc
Revises:
Create Date: 2026-02-23 20:17:18.143838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ea79cf6bfcdc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # BhavcopyEQ
    op.create_table(
        'bhavcopy_eq',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('series', sa.String(length=10), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('prev_close', sa.Float(), nullable=True),
        sa.Column('open_price', sa.Float(), nullable=True),
        sa.Column('high_price', sa.Float(), nullable=True),
        sa.Column('low_price', sa.Float(), nullable=True),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('close_price', sa.Float(), nullable=True),
        sa.Column('avg_price', sa.Float(), nullable=True),
        sa.Column('total_traded_qty', sa.Integer(), nullable=True),
        sa.Column('turnover_lacs', sa.Float(), nullable=True),
        sa.Column('no_of_trades', sa.Integer(), nullable=True),
        sa.Column('deliverable_qty', sa.Integer(), nullable=True),
        sa.Column('deliverable_pct', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('trade_date', 'id'),
        sa.UniqueConstraint('symbol', 'series', 'trade_date', name='uq_bhavcopy_eq_unique')
    )
    op.create_index('idx_bhavcopy_eq_symbol_date', 'bhavcopy_eq', ['symbol', 'trade_date'], unique=False)

    # BhavcopyFO
    op.create_table(
        'bhavcopy_fo',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('ticker_symb', sa.String(length=50), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('strike_price', sa.Float(), nullable=True),
        sa.Column('option_type', sa.String(length=5), nullable=True),
        sa.Column('instrument_name', sa.String(length=100), nullable=True),
        sa.Column('open_price', sa.Float(), nullable=True),
        sa.Column('high_price', sa.Float(), nullable=True),
        sa.Column('low_price', sa.Float(), nullable=True),
        sa.Column('close_price', sa.Float(), nullable=True),
        sa.Column('settle_price', sa.Float(), nullable=True),
        sa.Column('open_interest', sa.Integer(), nullable=True),
        sa.Column('change_in_oi', sa.Integer(), nullable=True),
        sa.Column('total_trading_vol', sa.Integer(), nullable=True),
        sa.Column('total_trf_val', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('trade_date', 'id'),
        sa.UniqueConstraint('trade_date', 'ticker_symb', 'expiry_date', 'strike_price', 'option_type', name='uq_bhavcopy_fo_unique')
    )
    op.create_index('idx_bhavcopy_fo_symbol_expiry', 'bhavcopy_fo', ['ticker_symb', 'expiry_date'], unique=False)

    # FAOParticipantOI
    op.create_table(
        'fao_participant_oi',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('client_type', sa.String(length=20), nullable=False),
        sa.Column('future_index_long', sa.Integer(), nullable=True),
        sa.Column('future_index_short', sa.Integer(), nullable=True),
        sa.Column('future_stock_long', sa.Integer(), nullable=True),
        sa.Column('future_stock_short', sa.Integer(), nullable=True),
        sa.Column('option_index_call_long', sa.Integer(), nullable=True),
        sa.Column('option_index_put_long', sa.Integer(), nullable=True),
        sa.Column('option_index_call_short', sa.Integer(), nullable=True),
        sa.Column('option_index_put_short', sa.Integer(), nullable=True),
        sa.Column('option_stock_call_long', sa.Integer(), nullable=True),
        sa.Column('option_stock_put_long', sa.Integer(), nullable=True),
        sa.Column('option_stock_call_short', sa.Integer(), nullable=True),
        sa.Column('option_stock_put_short', sa.Integer(), nullable=True),
        sa.Column('total_long_contracts', sa.Integer(), nullable=True),
        sa.Column('total_short_contracts', sa.Integer(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('trade_date', 'id'),
        sa.UniqueConstraint('trade_date', 'client_type', name='uq_fao_oi_unique')
    )

    # FOVolatility
    op.create_table(
        'fo_volatility',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('underlying_close_price', sa.Float(), nullable=True),
        sa.Column('underlying_annualised_vol', sa.Float(), nullable=True),
        sa.Column('futures_close_price', sa.Float(), nullable=True),
        sa.Column('futures_annualised_vol', sa.Float(), nullable=True),
        sa.Column('applicable_daily_vol', sa.Float(), nullable=True),
        sa.Column('applicable_annualised_vol', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('trade_date', 'id'),
        sa.UniqueConstraint('trade_date', 'symbol', name='uq_fo_volatility_unique')
    )

    # BlockDeal
    op.create_table(
        'block_deals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('security_name', sa.String(length=200), nullable=True),
        sa.Column('client_name', sa.String(length=200), nullable=True),
        sa.Column('buy_sell', sa.String(length=10), nullable=True),
        sa.Column('quantity_traded', sa.Integer(), nullable=True),
        sa.Column('trade_price', sa.Float(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'symbol', 'client_name', 'buy_sell', name='uq_block_deals_unique')
    )

    # BulkDeal
    op.create_table(
        'bulk_deals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('security_name', sa.String(length=200), nullable=True),
        sa.Column('client_name', sa.String(length=200), nullable=True),
        sa.Column('buy_sell', sa.String(length=10), nullable=True),
        sa.Column('quantity_traded', sa.Integer(), nullable=True),
        sa.Column('trade_price', sa.Float(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'symbol', 'client_name', 'buy_sell', name='uq_bulk_deals_unique')
    )

    # FIIDerivativesStat
    op.create_table(
        'fii_derivatives_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('instrument_type', sa.String(length=50), nullable=False),
        sa.Column('buy_contracts', sa.Integer(), nullable=True),
        sa.Column('buy_amt_crores', sa.Float(), nullable=True),
        sa.Column('sell_contracts', sa.Integer(), nullable=True),
        sa.Column('sell_amt_crores', sa.Float(), nullable=True),
        sa.Column('oi_contracts', sa.Integer(), nullable=True),
        sa.Column('oi_amt_crores', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'instrument_type', name='uq_fii_stats_unique')
    )

    # MTODelivery
    op.create_table(
        'mto_delivery',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('settlement_type', sa.String(length=10), nullable=True),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('security_name', sa.String(length=200), nullable=False),
        sa.Column('quantity_traded', sa.Integer(), nullable=True),
        sa.Column('deliverable_qty', sa.Integer(), nullable=True),
        sa.Column('deliverable_pct', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('trade_date', 'id'),
        sa.UniqueConstraint('trade_date', 'security_name', name='uq_mto_delivery_unique')
    )

    # MWPLClientPosition
    op.create_table(
        'mwpl_client_position',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('underlying_stock', sa.String(length=50), nullable=False),
        sa.Column('client_position_num', sa.Integer(), nullable=False),
        sa.Column('position_pct', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'underlying_stock', 'client_position_num', name='uq_mwpl_unique')
    )

    # SecurityMaster
    op.create_table(
        'security_master',
        sa.Column('fin_instrm_id', sa.String(length=50), nullable=False),
        sa.Column('ticker_symb', sa.String(length=50), nullable=False),
        sa.Column('security_series', sa.String(length=10), nullable=True),
        sa.Column('instrument_name', sa.String(length=200), nullable=True),
        sa.Column('isin', sa.String(length=20), nullable=True),
        sa.Column('new_brd_lot_qty', sa.Integer(), nullable=True),
        sa.Column('par_val', sa.Float(), nullable=True),
        sa.Column('issued_capital', sa.Float(), nullable=True),
        sa.Column('listed_date', sa.Date(), nullable=True),
        sa.Column('additional_info', sa.Text(), nullable=True),
        sa.Column('special_ex_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('fin_instrm_id'),
        sa.UniqueConstraint('isin')
    )
    op.create_index('idx_security_master_ticker', 'security_master', ['ticker_symb'], unique=False)

    # PERatio
    op.create_table(
        'pe_ratio',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('symbol_pe', sa.Float(), nullable=True),
        sa.Column('adjusted_pe', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'symbol', name='uq_pe_ratio_unique')
    )

    # ImportLog
    op.create_table(
        'import_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_date', sa.Date(), nullable=True),
        sa.Column('table_name', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('rows_inserted', sa.Integer(), nullable=True),
        sa.Column('rows_updated', sa.Integer(), nullable=True),
        sa.Column('error_msg', sa.Text(), nullable=True),
        sa.Column('source_file', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_import_logs_date', 'import_logs', ['import_date'], unique=False)
    op.create_index('idx_import_logs_table', 'import_logs', ['table_name'], unique=False)

    # SystemLog
    op.create_table(
        'system_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_syslog_source', 'system_logs', ['source'], unique=False)
    op.create_index('idx_syslog_ts_level', 'system_logs', ['timestamp', 'level'], unique=False)

    # VaRStat
    op.create_table(
        'var_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('series', sa.String(length=10), nullable=True),
        sa.Column('security_var', sa.Float(), nullable=True),
        sa.Column('index_var', sa.Float(), nullable=True),
        sa.Column('var_margin', sa.Float(), nullable=True),
        sa.Column('extreme_loss_rate', sa.Float(), nullable=True),
        sa.Column('adho_margin', sa.Float(), nullable=True),
        sa.Column('applicable_margin_rate', sa.Float(), nullable=True),
        sa.Column('file_type', sa.String(length=10), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'symbol', 'series', 'file_type', name='uq_var_stats_unique')
    )

    # ContractDelta
    op.create_table(
        'contract_delta',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('strike_price', sa.Float(), nullable=True),
        sa.Column('option_type', sa.String(length=5), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'symbol', 'expiry_date', 'strike_price', 'option_type', name='uq_contract_delta_unique')
    )

    # Auction
    op.create_table(
        'auctions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('series', sa.String(length=10), nullable=True),
        sa.Column('auction_qty', sa.Integer(), nullable=True),
        sa.Column('best_buy_price', sa.Float(), nullable=True),
        sa.Column('best_sell_price', sa.Float(), nullable=True),
        sa.Column('auction_price', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'symbol', 'series', name='uq_auctions_unique')
    )

    # MarginTrading
    op.create_table(
        'margin_trading',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('quantity_funded', sa.Integer(), nullable=True),
        sa.Column('amount_funded', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('date', 'id'),
        sa.UniqueConstraint('date', 'symbol', name='uq_margin_trading_unique')
    )

    # Convert to TimescaleDB Hypertables (if extension exists)
    # Note: We wrap in try/except block via PL/SQL or just attempt if we know extension is there.
    # For Alembic, usually we execute raw SQL.

    # We'll execute these conditionally or assume TimescaleDB is present as per requirement
    tables_to_convert = [
        ('bhavcopy_eq', 'trade_date'),
        ('bhavcopy_fo', 'trade_date'),
        ('fao_participant_oi', 'trade_date'),
        ('fo_volatility', 'trade_date'),
        ('block_deals', 'date'),
        ('bulk_deals', 'date'),
        ('fii_derivatives_stats', 'date'),
        ('mto_delivery', 'trade_date'),
        ('mwpl_client_position', 'date'),
        ('pe_ratio', 'date'),
        ('var_stats', 'date'),
        ('contract_delta', 'date'),
        ('auctions', 'date'),
        ('margin_trading', 'date'),
        ('system_logs', 'timestamp')
    ]

    for table, time_col in tables_to_convert:
        try:
            op.execute(f"SELECT create_hypertable('{table}', '{time_col}', if_not_exists => TRUE);")
        except Exception:
            # Fallback or ignore if Timescale not available/already created
            pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('import_logs')
    op.drop_table('pe_ratio')
    op.drop_table('security_master')
    op.drop_table('mwpl_client_position')
    op.drop_table('mto_delivery')
    op.drop_table('fii_derivatives_stats')
    op.drop_table('bulk_deals')
    op.drop_table('block_deals')
    op.drop_table('fo_volatility')
    op.drop_table('fao_participant_oi')
    op.drop_table('bhavcopy_fo')
    op.drop_table('bhavcopy_eq')
