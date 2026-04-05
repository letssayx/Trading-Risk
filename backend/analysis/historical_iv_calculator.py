import math
from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.infrastructure.db import get_db
from backend.ingest.nse_models import HistoricalATMIV
import numpy as np

def calculate_historical_atm_iv(db: Session, symbol: str, lookback_days: int = 500, force: bool = False):
    """
    Backfills or updates historical ATM IV for a given symbol up to `lookback_days` trading days.
    If `force=True`, recalculates for the entire window regardless of existing data.
    """
    symbol = symbol.upper()
    is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

    # 1. Find the target trading days
    # We fetch DESC with LIMIT, then reverse to ASC
    if is_index:
        query = text("""
            SELECT trade_date, close_price
            FROM historical_index_data
            WHERE index_name = :symbol
            ORDER BY trade_date DESC
            LIMIT :lookback
        """)
    else:
        query = text("""
            SELECT trade_date, close_price
            FROM bhavcopy_eq
            WHERE ticker_symb = :symbol AND series = 'EQ'
            ORDER BY trade_date DESC
            LIMIT :lookback
        """)

    result = db.execute(query, {"symbol": symbol, "lookback": lookback_days}).fetchall()

    # Fallback to futures if eq/index is empty
    if not result:
        try:
            query = text("""
                SELECT * FROM (
                    SELECT DISTINCT ON (trade_date) trade_date, close_price
                    FROM bhavcopy_fo
                    WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK', 'IDF', 'STF')
                    ORDER BY trade_date DESC, expiry_date ASC
                ) AS distinct_dates
                ORDER BY trade_date DESC
                LIMIT :lookback
            """)
            result = db.execute(query, {"symbol": symbol, "lookback": lookback_days}).fetchall()
        except Exception:
            db.rollback()
            result = []

    if not result:
        return 0

    result.reverse() # Sort ascending
    trading_days = {r[0]: float(r[1]) for r in result}

    # 2. Determine which dates are missing
    dates_to_calculate = []
    if force:
        dates_to_calculate = list(trading_days.keys())
        db.execute(text("DELETE FROM historical_atm_iv WHERE symbol = :symbol"), {"symbol": symbol})
        db.commit()
    else:
        # Check existing data
        existing_query = text("""
            SELECT trade_date FROM historical_atm_iv
            WHERE symbol = :symbol
            AND trade_date >= :min_date AND trade_date <= :max_date
        """)
        min_date = list(trading_days.keys())[0]
        max_date = list(trading_days.keys())[-1]
        existing_dates = set([r[0] for r in db.execute(existing_query, {"symbol": symbol, "min_date": min_date, "max_date": max_date}).fetchall()])

        dates_to_calculate = [d for d in trading_days.keys() if d not in existing_dates]

    if not dates_to_calculate:
        return 0

    from backend.risk.greeks import calculate_implied_volatility

    # 3. Calculate IV for missing dates
    inserted_count = 0
    batch_size = 50
    records = []

    # Using a single large query to fetch all required options data across these dates might be too large,
    # but querying per day might be too slow. Let's chunk the dates.
    for i in range(0, len(dates_to_calculate), batch_size):
        batch_dates = dates_to_calculate[i:i+batch_size]

        # CTE to find the nearest expiry for each trade_date
        opts_query = text("""
            WITH ExpiryRank AS (
                SELECT trade_date, expiry_date,
                       ROW_NUMBER() OVER(PARTITION BY trade_date ORDER BY expiry_date ASC) as rnk
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND trade_date = ANY(:dates)
                  AND expiry_date > trade_date
                  AND instrument_type IN ('OPTIDX', 'OPTSTK', 'STO', 'IDO')
            )
            SELECT bf.trade_date, bf.expiry_date, bf.strike_price, bf.option_type, bf.close_price
            FROM bhavcopy_fo bf
            JOIN ExpiryRank er ON bf.trade_date = er.trade_date AND bf.expiry_date = er.expiry_date AND er.rnk = 1
            WHERE bf.ticker_symb = :symbol
              AND bf.trade_date = ANY(:dates)
              AND bf.instrument_type IN ('OPTIDX', 'OPTSTK', 'STO', 'IDO')
        """)

        opts_result = db.execute(opts_query, {"symbol": symbol, "dates": batch_dates}).fetchall()

        # Group by trade_date
        opts_by_date = {}
        for r in opts_result:
            td = r[0]
            if td not in opts_by_date:
                opts_by_date[td] = []
            opts_by_date[td].append({
                "expiry_date": r[1],
                "strike_price": float(r[2]),
                "option_type": r[3],
                "close_price": float(r[4])
            })

        for t_date in batch_dates:
            underlying_price = trading_days[t_date]
            opts = opts_by_date.get(t_date, [])

            if not opts or underlying_price <= 0:
                continue

            nearest_expiry = opts[0]["expiry_date"]
            current_dte = (nearest_expiry - t_date).days

            if current_dte <= 0:
                continue

            t_years = current_dte / 365.0
            risk_free_rate = 0.05

            # Find ATM strike
            strikes = sorted(list(set([o["strike_price"] for o in opts])))
            if not strikes:
                continue
            atm_strike = min(strikes, key=lambda x: abs(x - underlying_price))

            atm_call_px = None
            atm_put_px = None

            for o in opts:
                if o["strike_price"] == atm_strike:
                    if o["option_type"] == 'CE': atm_call_px = o["close_price"]
                    elif o["option_type"] == 'PE': atm_put_px = o["close_price"]

            ivs = []
            if atm_call_px and atm_call_px > 0:
                call_iv = calculate_implied_volatility(atm_call_px, underlying_price, atm_strike, t_years, risk_free_rate, 'call')
                if call_iv and 0 < call_iv < 2.0: # Sanity check, ignore crazy IVs > 200%
                    ivs.append(call_iv * 100)

            if atm_put_px and atm_put_px > 0:
                put_iv = calculate_implied_volatility(atm_put_px, underlying_price, atm_strike, t_years, risk_free_rate, 'put')
                if put_iv and 0 < put_iv < 2.0:
                    ivs.append(put_iv * 100)

            if ivs:
                real_iv = sum(ivs) / len(ivs)
                records.append({
                    "trade_date": t_date,
                    "symbol": symbol,
                    "atm_iv": real_iv
                })
                inserted_count += 1

        # Insert batch
        if records:
            db.bulk_insert_mappings(HistoricalATMIV, records)
            db.commit()
            records = []

    return inserted_count
