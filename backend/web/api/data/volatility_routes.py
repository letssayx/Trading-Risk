from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.infrastructure.db import get_db
import math
import numpy as np

router = APIRouter()

@router.get("/api/data/derivatives/volatility_cone/{symbol}")
async def get_volatility_cone(symbol: str, db: Session = Depends(get_db)):
    try:
        symbol = symbol.upper()
        is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

        # Fetch historical prices to calculate realized volatility
        if is_index:
            query = text("""
                SELECT trade_date, close_price
                FROM historical_index_data
                WHERE index_name = :symbol
                ORDER BY trade_date ASC
            """)
        else:
            query = text("""
                SELECT trade_date, close_price
                FROM bhavcopy_eq
                WHERE ticker_symb = :symbol AND series = 'EQ'
                ORDER BY trade_date ASC
            """)

        result = db.execute(query, {"symbol": symbol}).fetchall()

        # fallback to futures if eq/index is empty
        if not result:
             try:
                 query = text("""
                    SELECT * FROM (
                        SELECT DISTINCT ON (trade_date) trade_date, close_price
                        FROM bhavcopy_fo
                        WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK', 'IDF', 'STF')
                        ORDER BY trade_date ASC, expiry_date ASC
                    ) AS distinct_dates
                    ORDER BY trade_date ASC
                """)
                 result = db.execute(query, {"symbol": symbol}).fetchall()
             except Exception:
                 db.rollback()
                 result = []

        if not result or len(result) < 5:
            raise HTTPException(status_code=400, detail=f"Insufficient price history for Volatility Cone ({len(result)} records found, need at least 5 days)")

        dates = [r[0] for r in result]
        prices = [float(r[1]) for r in result]

        # Calculate daily log returns
        log_returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0 and prices[i] > 0:
                log_returns.append(math.log(prices[i] / prices[i-1]))
            else:
                log_returns.append(0.0)

        # Windows to calculate
        windows = [3, 7, 10, 20, 30, 60, 90, 252, 500]

        cone_data = {
            "windows": windows,
            "min": [],
            "max": [],
            "p25": [],
            "p50": [],
            "p75": [],
            "current_rv": [] # Current realized vol for that window ending today
        }

        # Fetch the underlying price for the current date to determine ATM strikes
        current_date = dates[-1]
        underlying_price = prices[-1]

        # Fetch options data for the current date to calculate ATM IV dynamically
        real_iv = None
        try:
            from backend.risk.greeks import calculate_implied_volatility

            # 1. Find the nearest valid expiry date
            expiry_query = text("""
                SELECT MIN(expiry_date)
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND trade_date = :current_date
                  AND expiry_date > :current_date
                  AND instrument_type IN ('OPTIDX', 'OPTSTK', 'STO', 'IDO')
            """)
            nearest_expiry = db.execute(expiry_query, {"symbol": symbol, "current_date": current_date}).scalar()

            if nearest_expiry and underlying_price > 0:
                dte = (nearest_expiry - current_date).days
                if dte > 0:
                    t_years = dte / 365.0
                    risk_free_rate = 0.05

                    # 2. Get options for this expiry
                    opts_query = text("""
                        SELECT strike_price, option_type, close_price
                        FROM bhavcopy_fo
                        WHERE ticker_symb = :symbol
                          AND trade_date = :current_date
                          AND expiry_date = :nearest_expiry
                          AND instrument_type IN ('OPTIDX', 'OPTSTK', 'STO', 'IDO')
                    """)
                    opts_result = db.execute(opts_query, {
                        "symbol": symbol,
                        "current_date": current_date,
                        "nearest_expiry": nearest_expiry
                    }).fetchall()

                    if opts_result:
                        # Find nearest ATM strike
                        strikes = sorted(list(set([r[0] for r in opts_result])))
                        atm_strike = min(strikes, key=lambda x: abs(x - underlying_price))

                        atm_call_px = None
                        atm_put_px = None

                        for r in opts_result:
                            if r[0] == atm_strike:
                                if r[1] == 'CE': atm_call_px = float(r[2])
                                elif r[1] == 'PE': atm_put_px = float(r[2])

                        ivs = []
                        if atm_call_px and atm_call_px > 0:
                            call_iv = calculate_implied_volatility(atm_call_px, underlying_price, atm_strike, t_years, risk_free_rate, 'c')
                            if call_iv: ivs.append(call_iv * 100) # convert to percentage

                        if atm_put_px and atm_put_px > 0:
                            put_iv = calculate_implied_volatility(atm_put_px, underlying_price, atm_strike, t_years, risk_free_rate, 'p')
                            if put_iv: ivs.append(put_iv * 100)

                        if ivs:
                            real_iv = sum(ivs) / len(ivs)

        except Exception as e:
            print(f"Failed to calculate dynamic IV for cone: {e}")
            real_iv = None

        for w in windows:
            if w > len(log_returns):
                # Fill with none or 0
                cone_data["min"].append(None)
                cone_data["max"].append(None)
                cone_data["p25"].append(None)
                cone_data["p50"].append(None)
                cone_data["p75"].append(None)
                cone_data["current_rv"].append(None)
                continue

            # Calculate rolling RV for window w
            rolling_rv = []
            # Annualization factor = sqrt(252)
            ann_factor = math.sqrt(252)

            for i in range(len(log_returns) - w + 1):
                window_returns = log_returns[i:i+w]
                # Sample standard deviation
                if len(window_returns) > 1:
                    mean_r = sum(window_returns) / len(window_returns)
                    var_r = sum((r - mean_r)**2 for r in window_returns) / (len(window_returns) - 1)
                    rv = math.sqrt(var_r) * ann_factor * 100 # percentage
                    rolling_rv.append(rv)

            if rolling_rv:
                cone_data["min"].append(round(min(rolling_rv), 2))
                cone_data["max"].append(round(max(rolling_rv), 2))
                cone_data["p25"].append(round(float(np.percentile(rolling_rv, 25)), 2))
                cone_data["p50"].append(round(float(np.percentile(rolling_rv, 50)), 2))
                cone_data["p75"].append(round(float(np.percentile(rolling_rv, 75)), 2))

                # Use real options IV if available, otherwise fallback to the most recent RV to avoid hallucinating fake values.
                cone_data["current_rv"].append(round(real_iv, 2) if real_iv else round(rolling_rv[-1], 2))
            else:
                cone_data["min"].append(None)
                cone_data["max"].append(None)
                cone_data["p25"].append(None)
                cone_data["p50"].append(None)
                cone_data["p75"].append(None)
                cone_data["current_rv"].append(None)

        return cone_data
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/data/derivatives/pre_expiry_action/{symbol}")
async def get_pre_expiry_action(
    symbol: str,
    lookback_days: int = 500,
    box_days: int = 7,
    expiry_type: str = "monthly",
    db: Session = Depends(get_db)
):
    try:
        symbol = symbol.upper()

        # 1. Fetch underlying price history
        query = text("""
            SELECT trade_date, close_price
            FROM bhavcopy_eq
            WHERE ticker_symb = :symbol
            ORDER BY trade_date DESC
            LIMIT :lookback
        """)
        is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

        try:
            if is_index:
                idx_query = text("""
                    SELECT trade_date, close_price
                    FROM historical_index_data
                    WHERE index_name = :symbol
                    ORDER BY trade_date DESC
                    LIMIT :lookback
                """)
                result = db.execute(idx_query, {"symbol": symbol, "lookback": lookback_days}).fetchall()
            else:
                query = text("""
                    SELECT trade_date, close_price
                    FROM bhavcopy_eq
                    WHERE ticker_symb = :symbol AND series = 'EQ'
                    ORDER BY trade_date DESC
                    LIMIT :lookback
                """)
                result = db.execute(query, {"symbol": symbol, "lookback": lookback_days}).fetchall()
        except Exception:
            db.rollback()
            result = []

        if not result:
             db.rollback()
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

        result.reverse() # Sort ascending

        if not result:
            return {"detail": "No price data found for the given symbol.", "dates": [], "prices": [], "expiries": [], "rv": [], "boxes": []}

        dates = [r[0].strftime('%Y-%m-%d') for r in result]
        prices = [float(r[1]) for r in result]

        # Calculate Rolling Realized Volatility for the box_days window
        rv_line = []
        log_returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0 and prices[i] > 0:
                log_returns.append(math.log(prices[i] / prices[i-1]))
            else:
                log_returns.append(0.0)

        ann_factor = math.sqrt(252)
        for i in range(len(prices)):
            if i < box_days:
                rv_line.append(None)
            else:
                window_returns = log_returns[i-box_days:i]
                if len(window_returns) > 1:
                    mean_r = sum(window_returns) / len(window_returns)
                    var_r = sum((r - mean_r)**2 for r in window_returns) / (len(window_returns) - 1)
                    rv = math.sqrt(var_r) * ann_factor * 100
                    rv_line.append(round(rv, 2))
                else:
                    rv_line.append(None)

        # 2. Fetch Expiry Dates within the timeframe
        min_date = dates[0]
        max_date = dates[-1]

        expiry_query = text("""
            SELECT DISTINCT trade_date, expiry_date, instrument_type
            FROM bhavcopy_fo
            WHERE ticker_symb = :symbol
              AND trade_date >= :min_date AND trade_date <= :max_date
        """)
        expiry_result = db.execute(expiry_query, {"symbol": symbol, "min_date": min_date, "max_date": max_date}).fetchall()

        # We need to find the actual expiry dates that happened.
        # An expiry happens on a date if there is a trade_date == expiry_date
        expiries = set()
        for r in expiry_result:
            t_date = r[0].strftime('%Y-%m-%d')
            e_date = r[1].strftime('%Y-%m-%d')
            i_type = r[2]

            if t_date == e_date:
                # Is it monthly or weekly?
                # Monthly usually has FUTIDX/FUTSTK expiring
                # Weekly usually only has OPTIDX (for indexes) expiring

                is_monthly = i_type in ['FUTIDX', 'FUTSTK', 'STF', 'IDF']
                is_options = i_type in ['OPTIDX', 'OPTSTK', 'STO', 'IDO']

                if expiry_type.lower() == 'monthly' and is_monthly:
                    expiries.add(e_date)
                elif expiry_type.lower() == 'weekly' and is_options:
                    # Both monthly and weekly options expire, so we include them
                    expiries.add(e_date)

        sorted_expiries = sorted(list(expiries))

        # 3. Build boxes
        boxes = []
        for exp in sorted_expiries:
            if exp in dates:
                exp_idx = dates.index(exp)
                start_idx = max(0, exp_idx - box_days)

                boxes.append({
                    "start_date": dates[start_idx],
                    "end_date": dates[exp_idx]
                })

        return {
            "dates": dates,
            "prices": prices,
            "rv": rv_line,
            "expiries": sorted_expiries,
            "boxes": boxes
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
