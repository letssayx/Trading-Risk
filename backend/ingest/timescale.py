"""TimescaleDB Utilities"""
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.config.defaults.nse import TIMESCALE_RETENTION, TIMESCALE_COMPRESSION_AFTER_DAYS

logger = logging.getLogger(__name__)

HYPERTABLES = [
    "bhavcopy_eq",
    "bhavcopy_fo",
    "fao_participant_oi",
    "fo_volatility",
    "block_deals",
    "bulk_deals",
    "fii_derivatives_stats",
    "mto_delivery",
    "mwpl_client_position",
    "pe_ratio",
]


def ensure_hypertable(db: Session, table_name: str, time_column: str = "trade_date") -> bool:
    """Create hypertable if not exists (idempotent)."""
    try:
        # Handle tables with 'date' instead of 'trade_date'
        if table_name in ["block_deals", "bulk_deals", "fii_derivatives_stats", "mwpl_client_position", "pe_ratio"]:
            time_column = "date"
        elif table_name == "mto_delivery":
            time_column = "trade_date"

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


def set_compression_policy(db: Session, table_name: str, after_days: int = None) -> bool:
    """Enable compression for hypertable."""
    after_days = after_days or TIMESCALE_COMPRESSION_AFTER_DAYS
    try:
        db.execute(text(f"""
            ALTER TABLE {table_name} SET (
                timescaledb.compress,
                timescaledb.compress_orderby = '{table_name.replace("bhavcopy_", "")}_date DESC, symbol',
                timescaledb.compress_segmentby = 'symbol'
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


def set_retention_policy(db: Session, table_name: str, keep_days: int = None) -> bool:
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


def setup_all_timescale_policies(db: Session) -> dict:
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
