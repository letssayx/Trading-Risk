"""TimescaleDB-Optimized Query Helpers"""
from datetime import date, timedelta
from typing import Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd


def get_bhavcopy_eq_timeseries(
    db: Session,
    symbol: str,
    start_date: date,
    end_date: date,
    resample: str = '1 day'
) -> list[dict[str, Any]]:
    """Query equity bhavcopy with time_bucket resampling."""
    query = text("""
        SELECT
            time_bucket(:resample, trade_date) AS period,
            symbol,
            FIRST(close_price, trade_date) AS period_open,
            MAX(high_price) AS period_high,
            MIN(low_price) AS period_low,
            LAST(close_price, trade_date) AS period_close,
            SUM(total_traded_qty) AS period_volume,
            AVG(deliverable_pct) AS avg_deliverable_pct
        FROM bhavcopy_eq
        WHERE symbol = :symbol
          AND trade_date BETWEEN :start_date AND :end_date
        GROUP BY period, symbol
        ORDER BY period DESC
    """)

    result = db.execute(query, {
        'resample': resample,
        'symbol': symbol,
        'start_date': start_date,
        'end_date': end_date
    })
    # Use _mapping for safer dict conversion in SQLAlchemy 1.4+
    return [dict(row._mapping) for row in result]


def get_fno_oi_trend(
    db: Session,
    symbol: str,
    expiry_date: date | None = None,
    lookback_days: int = 30
) -> dict[str, Any]:
    """Get F&O OI trend using continuous aggregate (fallback to raw)."""

    cutoff_date = date.today() - timedelta(days=lookback_days)

    # Try continuous aggregate first
    try:
        agg_query = text("""
            SELECT
                bucket AS trade_date,
                total_oi,
                net_oi_change,
                total_volume
            FROM fno_daily_oi_summary
            WHERE ticker_symb = :symbol
              AND (:expiry IS NULL OR expiry_date = :expiry)
              AND bucket >= :cutoff_date
            ORDER BY bucket DESC
        """)

        result = db.execute(agg_query, {
            'symbol': symbol,
            'expiry': expiry_date,
            'cutoff_date': cutoff_date
        }).fetchall()

        if result:
            return {
                'source': 'continuous_aggregate',
                'data': [dict(row._mapping) for row in result],
                'symbol': symbol,
                'expiry': expiry_date.isoformat() if expiry_date else None
            }
    except Exception:
        pass

    # Fallback to raw table
    raw_query = text("""
        SELECT
            trade_date,
            SUM(open_interest) AS total_oi,
            SUM(change_in_oi) AS net_oi_change,
            SUM(total_trading_vol) AS total_volume
        FROM bhavcopy_fo
        WHERE ticker_symb = :symbol
          AND (:expiry IS NULL OR expiry_date = :expiry)
          AND trade_date >= :cutoff_date
        GROUP BY trade_date
        ORDER BY trade_date DESC
    """)

    result = db.execute(raw_query, {
        'symbol': symbol,
        'expiry': expiry_date,
        'cutoff_date': cutoff_date
    }).fetchall()

    return {
        'source': 'raw_table',
        'data': [dict(row._mapping) for row in result],
        'symbol': symbol,
        'expiry': expiry_date.isoformat() if expiry_date else None
    }


def get_volatility_comparison(
    db: Session,
    symbols: List[str],
    days: int = 90
) -> pd.DataFrame:
    """Compare volatility across symbols."""
    cutoff_date = date.today() - timedelta(days=days)

    query = text("""
        SELECT
            trade_date,
            symbol,
            applicable_annualised_vol AS ann_vol,
            underlying_close_price AS price
        FROM fo_volatility
        WHERE symbol = ANY(:symbols)
          AND trade_date >= :cutoff_date
        ORDER BY trade_date DESC, symbol
    """)

    result = db.execute(query, {'symbols': symbols, 'cutoff_date': cutoff_date})
    return pd.DataFrame(result.fetchall(), columns=result.keys())


def get_participant_oi_heatmap(
    db: Session,
    trade_date: date | None = None
) -> dict[str, Any]:
    """Get participant-wise OI heatmap."""
    target_date = trade_date or (date.today() - timedelta(days=1))

    query = text("""
        SELECT
            client_type,
            future_index_long, future_index_short,
            future_stock_long, future_stock_short,
            option_index_call_long, option_index_put_long,
            option_index_call_short, option_index_put_short,
            option_stock_call_long, option_stock_put_long,
            option_stock_call_short, option_stock_put_short,
            total_long_contracts, total_short_contracts,
            (total_long_contracts - total_short_contracts) AS net_position
        FROM fao_participant_oi
        WHERE trade_date = :target_date
        ORDER BY
            CASE client_type
                WHEN 'FII' THEN 1
                WHEN 'DII' THEN 2
                WHEN 'Pro' THEN 3
                WHEN 'Client' THEN 4
                ELSE 5
            END
    """)

    result = db.execute(query, {'target_date': target_date})

    return {
        'date': target_date.isoformat(),
        'participants': [dict(row._mapping) for row in result]
    }


def get_import_stats(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None
) -> dict[str, Any]:
    """Get import job statistics.
    Updated to return max dates (data date) and max download times (created_at).
    """
    query = text("""
        SELECT
            table_name,
            status,
            COUNT(*) as job_count,
            SUM(rows_inserted) as total_rows,
            MAX(import_date) as last_import_date,
            MAX(created_at) as last_download_time
        FROM import_logs
        WHERE (:start IS NULL OR import_date >= :start)
          AND (:end IS NULL OR import_date <= :end)
        GROUP BY table_name, status
        ORDER BY table_name, status
    """)

    result = db.execute(query, {'start': start_date, 'end': end_date})

    return {
        'summary': [dict(row._mapping) for row in result],
        'period': {'start': start_date.isoformat() if start_date else None,
                   'end': end_date.isoformat() if end_date else None}
    }
