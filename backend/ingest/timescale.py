"""TimescaleDB Utilities"""
import logging
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.config.defaults.nse import TIMESCALE_RETENTION, TIMESCALE_COMPRESSION_AFTER_DAYS

logger = logging.getLogger(__name__)

# Configuration for TimescaleDB tables
# Format: table_name: (time_column, segment_column)
# segment_column is used for compression segmentation. If None, compression might skip segmentby.
TABLE_CONFIG: Dict[str, tuple[str, str]] = {
    "bhavcopy_eq": ("trade_date", "symbol"),
    "bhavcopy_fo": ("trade_date", "ticker_symb"), # ticker_symb is the symbol col in FO
    "fao_participant_oi": ("trade_date", "client_type"),
    "fo_volatility": ("trade_date", "symbol"),
    "block_deals": ("date", "symbol"),
    "bulk_deals": ("date", "symbol"),
    "fii_derivatives_stats": ("date", "instrument_type"),
    "mto_delivery": ("trade_date", "security_name"),
    "mwpl_client_position": ("date", "underlying_stock"),
    "pe_ratio": ("date", "symbol"),
}

HYPERTABLES = list(TABLE_CONFIG.keys())


def ensure_hypertable(db: Session, table_name: str) -> bool:
    """Create hypertable if not exists (idempotent)."""
    try:
        config = TABLE_CONFIG.get(table_name)
        if not config:
            logger.error(f"No config for table {table_name}")
            return False

        time_column, _ = config

        db.execute(text(f"""
            SELECT create_hypertable('{table_name}', '{time_column}',
                if_not_exists => TRUE,
                chunk_time_interval => INTERVAL '7 days')
        """))
        db.commit()
        logger.info(f"✓ Hypertable ensured: {table_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create hypertable {table_name}: {e}")
        db.rollback()
        return False


def set_compression_policy(db: Session, table_name: str, after_days: int | None = None) -> bool:
    """Enable compression for hypertable."""
    after_days = after_days or TIMESCALE_COMPRESSION_AFTER_DAYS
    try:
        config = TABLE_CONFIG.get(table_name)
        if not config:
            return False

        time_column, segment_column = config

        # Build compression settings
        segment_by_clause = f", timescaledb.compress_segmentby = '{segment_column}'" if segment_column else ""

        # Order by time desc, then segment (common pattern)
        order_by_clause = f"timescaledb.compress_orderby = '{time_column} DESC'"
        if segment_column:
             order_by_clause = f"timescaledb.compress_orderby = '{time_column} DESC, {segment_column}'"

        db.execute(text(f"""
            ALTER TABLE {table_name} SET (
                timescaledb.compress,
                {order_by_clause}
                {segment_by_clause}
            )
        """))

        db.execute(text(f"""
            SELECT add_compression_policy('{table_name}', INTERVAL '{after_days} days', if_not_exists => TRUE)
        """))
        db.commit()
        logger.info(f"✓ Compression policy set: {table_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to set compression for {table_name}: {e}")
        db.rollback()
        return False


def set_retention_policy(db: Session, table_name: str, keep_days: int | None = None) -> bool:
    """Set data retention policy."""
    keep_days = TIMESCALE_RETENTION.get(table_name, keep_days)
    if keep_days is None:
        logger.info(f"⊘ Skipping retention for {table_name} (keep forever)")
        return True

    try:
        db.execute(text(f"""
            SELECT add_retention_policy('{table_name}', INTERVAL '{keep_days} days', if_not_exists => TRUE)
        """))
        db.commit()
        logger.info(f"✓ Retention policy set: {table_name} ({keep_days} days)")
        return True
    except Exception as e:
        logger.error(f"Failed to set retention for {table_name}: {e}")
        db.rollback()
        return False


def create_continuous_aggregates(db: Session) -> bool:
    """Create continuous aggregates for F&O OI."""
    try:
        db.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS fno_daily_oi_summary
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('1 day', trade_date) AS bucket,
                ticker_symb,
                expiry_date,
                option_type,
                SUM(open_interest) AS total_oi,
                SUM(change_in_oi) AS net_oi_change,
                SUM(total_trading_vol) AS total_volume
            FROM bhavcopy_fo
            GROUP BY bucket, ticker_symb, expiry_date, option_type
            WITH NO DATA
        """))

        db.execute(text("""
            SELECT add_continuous_aggregate_policy('fno_daily_oi_summary',
                start_offset => INTERVAL '365 days',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '1 hour',
                if_not_exists => TRUE)
        """))

        db.commit()
        logger.info("✓ Continuous aggregates created")
        return True
    except Exception as e:
        logger.error(f"Failed to create aggregates: {e}")
        db.rollback()
        return False


def setup_all_timescale_policies(db: Session) -> dict[str, Any]:
    """Run all TimescaleDB setup operations."""
    results = {"hypertables": 0, "compression": 0, "retention": 0, "aggregates": False}

    for table in HYPERTABLES:
        if ensure_hypertable(db, table):
            results["hypertables"] += 1
        if set_compression_policy(db, table):
            results["compression"] += 1
        if set_retention_policy(db, table):
            results["retention"] += 1

    results["aggregates"] = create_continuous_aggregates(db)
    return results
