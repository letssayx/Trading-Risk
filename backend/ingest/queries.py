"""TimescaleDB-Optimized Query Helpers"""
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd


def get_bhavcopy_eq_timeseries(
    db: Session,
    symbol: str,
    start_date: date,
    end_date: date,
    resample: str = '1 day'
) -> List[Dict]:
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
    return [dict(row) for row in result]


def get_fno_oi_trend(
    db: Session,
    symbol: str,
    expiry_date: Optional[date] = None,
    lookback_days: int = 30
) -> Dict:
    """Get F&O OI trend using continuous aggregate (fallback to raw)."""
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
              AND bucket >= CURRENT_DATE - INTERVAL ':lookback days'
            ORDER BY bucket DESC
        """)

        result = db.execute(agg_query, {
            'symbol': symbol,
            'expiry': expiry_date,
            'lookback': lookback_days
        }).fetchall()

        if result:
            return {
                'source': 'continuous_aggregate',
                'data': [dict(row) for row in result],
                'symbol': symbol,
                'expiry': expiry_date.isoformat() if expiry_date else None
            }
    except:
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
          AND trade_date >= CURRENT_DATE - INTERVAL ':lookback days'
        GROUP BY trade_date
        ORDER BY trade_date DESC
    """)

    result = db.execute(raw_query, {
        'symbol': symbol,
        'expiry': expiry_date,
        'lookback': lookback_days
    }).fetchall()

    return {
        'source': 'raw_table',
        'data': [dict(row) for row in result],
        'symbol': symbol,
        'expiry': expiry_date.isoformat() if expiry_date else None
    }


def get_volatility_comparison(
    db: Session,
    symbols: List[str],
    days: int = 90
) -> pd.DataFrame:
    """Compare volatility across symbols."""
    query = text("""
        SELECT
            trade_date,
            symbol,
            applicable_annualised_vol AS ann_vol,
            underlying_close_price AS price
        FROM fo_volatility
        WHERE symbol = ANY(:symbols)
          AND trade_date >= CURRENT_DATE - INTERVAL ':days days'
        ORDER BY trade_date DESC, symbol
    """)

    result = db.execute(query, {'symbols': symbols, 'days': days})
    return pd.DataFrame(result.fetchall(), columns=result.keys())


def get_participant_oi_heatmap(
    db: Session,
    trade_date: Optional[date] = None
) -> Dict:
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
        'participants': [dict(row) for row in result]
    }


def get_import_stats(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """Get import job statistics."""
    query = text("""
        SELECT
            table_name,
            status,
            COUNT(*) as job_count,
            SUM(rows_inserted) as total_rows
        FROM import_logs
        WHERE (:start IS NULL OR import_date >= :start)
          AND (:end IS NULL OR import_date <= :end)
        GROUP BY table_name, status
        ORDER BY table_name, status
    """)

    result = db.execute(query, {'start': start_date, 'end': end_date})

    return {
        'summary': [dict(row) for row in result],
        'period': {'start': start_date.isoformat() if start_date else None,
                   'end': end_date.isoformat() if end_date else None}
    }
