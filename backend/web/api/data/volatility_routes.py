from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.infrastructure.db import get_db
import math
import numpy as np

router = APIRouter()


@router.get("/api/data/derivatives/volatility_cone/{symbol}")
def get_volatility_cone(symbol: str, lookback_days: int = 500, force_calc: bool = False, db: Session = Depends(get_db)):
    try:
        symbol = symbol.upper()
        is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

        # Backfill historical IV if necessary
        try:
            from backend.analysis.historical_iv_calculator import calculate_historical_atm_iv
            calculate_historical_atm_iv(db, symbol, lookback_days=lookback_days, force=force_calc)
        except Exception as e:
            print(f"Warning: Failed to backfill historical ATM IV for {symbol}: {e}")
            import traceback
            traceback.print_exc()

        # Fetch historical prices to calculate realized volatility
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

        # fallback to futures if eq/index is empty
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

        result.reverse() # Sort ascending after applying limit

        if not result or len(result) < 5:
            raise HTTPException(status_code=400, detail=f"Insufficient price history for Volatility Cone ({len(result)} records found, need at least 5 days)")

        dates = [r[0] for r in result]
        prices = [float(r[1]) for r in result]

        # Get historical OHLC prices
        if is_index:
            ohlc_query = text("""
                SELECT trade_date, open_price, high_price, low_price, close_price
                FROM historical_index_data
                WHERE index_name = :symbol
                ORDER BY trade_date DESC
                LIMIT :lookback
            """)
        else:
            ohlc_query = text("""
                SELECT trade_date, open_price, high_price, low_price, close_price
                FROM bhavcopy_eq
                WHERE ticker_symb = :symbol AND series = 'EQ'
                ORDER BY trade_date DESC
                LIMIT :lookback
            """)

        ohlc_result = db.execute(ohlc_query, {"symbol": symbol, "lookback": lookback_days}).fetchall()

        if not ohlc_result:
            try:
                 ohlc_query = text("""
                    SELECT * FROM (
                        SELECT DISTINCT ON (trade_date) trade_date, open_price, high_price, low_price, close_price
                        FROM bhavcopy_fo
                        WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK', 'IDF', 'STF')
                        ORDER BY trade_date DESC, expiry_date ASC
                    ) AS distinct_dates
                    ORDER BY trade_date DESC
                    LIMIT :lookback
                """)
                 ohlc_result = db.execute(ohlc_query, {"symbol": symbol, "lookback": lookback_days}).fetchall()
            except Exception:
                 db.rollback()
                 ohlc_result = []

        ohlc_result.reverse()

        if not ohlc_result or len(ohlc_result) < 5:
            raise HTTPException(status_code=400, detail=f"Insufficient price history for Volatility Cone ({len(ohlc_result)} records found, need at least 5 days)")

        # Windows to calculate (updated per user request)
        windows = [1, 2, 3, 5, 10, 21, 30]

        cone_data = {
            "windows": windows,
            "p5": [],
            "p25": [],
            "p50": [],
            "p75": [],
            "p95": [],
            "current_rv": [], # Current realized vol for that window ending today
            "active_expiries": [] # To hold overlay dots
        }

        # Compute Garman-Klass Volatility
        ann_factor = math.sqrt(252) # User requested sqrt(252) for trading days

        # O, H, L, C arrays
        opens = np.array([float(r[1]) if r[1] > 0 else float(r[4]) for r in ohlc_result])
        highs = np.array([float(r[2]) if r[2] > 0 else float(r[4]) for r in ohlc_result])
        lows = np.array([float(r[3]) if r[3] > 0 else float(r[4]) for r in ohlc_result])
        closes = np.array([float(r[4]) for r in ohlc_result])

        # Calculate daily Garman-Klass variance estimator
        # 0.5 * (ln(H/L))^2 - (2ln2 - 1) * (ln(C/O))^2
        gk_daily_var = 0.5 * (np.log(highs / lows) ** 2) - (2 * math.log(2) - 1) * (np.log(closes / opens) ** 2)

        # Filter out negative variances (numerical instability)
        gk_daily_var = np.maximum(gk_daily_var, 0)

        # DO NOT filter out flat days globally, we must preserve chronology for rolling sums
        # We roll first, then calculate percentiles from valid rolling values

        import pandas as pd
        df = pd.DataFrame({'gk_var': gk_daily_var})

        for w in windows:
            # Step 2: Rolling SUM of variances over N days (forward horizon)
            rolling_var_sum = df['gk_var'].rolling(window=w).sum()

            # Step 3: Annualize to get volatility for N-day period
            # Formula: Vol_N = sqrt(Sum_of_variances * (252 / N)) * 100
            rolling_vol_annualized = np.sqrt(rolling_var_sum * (252 / w)) * 100

            # Step 4: Get percentiles from historical data
            valid_vol = rolling_vol_annualized.dropna().tail(lookback_days)

            if len(valid_vol) > 0:
                cone_data["p5"].append(round(float(valid_vol.quantile(0.05)), 2))
                cone_data["p25"].append(round(float(valid_vol.quantile(0.25)), 2))
                cone_data["p50"].append(round(float(valid_vol.quantile(0.50)), 2))
                cone_data["p75"].append(round(float(valid_vol.quantile(0.75)), 2))
                cone_data["p95"].append(round(float(valid_vol.quantile(0.95)), 2))
                cone_data["current_rv"].append(round(float(valid_vol.iloc[-1]), 2))
            else:
                cone_data["p5"].append(None)
                cone_data["p25"].append(None)
                cone_data["p50"].append(None)
                cone_data["p75"].append(None)
                cone_data["p95"].append(None)
                cone_data["current_rv"].append(None)


        # Fetch Active Expiries and their ATM IVs
        current_date = dates[-1]
        underlying_price = prices[-1]

        try:
            from backend.risk.greeks import calculate_implied_volatility
            # Nifty Weekly + All Monthly contracts = 'OPTIDX' / 'OPTSTK' / 'STO' / 'IDO'
            # We fetch all expiries > current_date
            combined_query = text("""
                SELECT expiry_date, strike_price, option_type, close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND trade_date = :current_date
                  AND expiry_date > :current_date
                  AND instrument_type IN ('OPTIDX', 'OPTSTK', 'STO', 'IDO')
            """)
            opts_result = db.execute(combined_query, {"symbol": symbol, "current_date": current_date}).fetchall()

            # Group by expiry
            expiries_map = {}
            for r in opts_result:
                exp_d = r[0]
                if exp_d not in expiries_map:
                    expiries_map[exp_d] = []
                expiries_map[exp_d].append({
                    "strike_price": float(r[1]),
                    "option_type": r[2],
                    "close_price": float(r[3])
                })

            active_expiries = []
            for exp_d, opts in expiries_map.items():
                current_dte = (exp_d - current_date).days
                if current_dte <= 0: continue

                t_years = current_dte / 365.0
                risk_free_rate = 0.05

                strikes = sorted(list(set([o["strike_price"] for o in opts])))
                if not strikes: continue
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
                    if call_iv and 0 < call_iv < 2.0: ivs.append(call_iv * 100)

                if atm_put_px and atm_put_px > 0:
                    put_iv = calculate_implied_volatility(atm_put_px, underlying_price, atm_strike, t_years, risk_free_rate, 'put')
                    if put_iv and 0 < put_iv < 2.0: ivs.append(put_iv * 100)

                if ivs:
                    real_iv = sum(ivs) / len(ivs)
                    active_expiries.append({
                        "expiry_date": exp_d.strftime('%Y-%m-%d'),
                        "dte": current_dte,
                        "atm_iv": float(round(real_iv, 2))
                    })

            cone_data["active_expiries"] = sorted(active_expiries, key=lambda x: x["dte"])

        except Exception as e:
            print(f"Failed to calculate active expiries IV for cone: {e}")

        # Fetch Historical ATM IV to calculate IVR and IVP
        cone_data["iv_summary"] = {
            "symbol": symbol,
            "price": round(underlying_price, 2),
            "current_atm_iv": None,
            "ivr": None,
            "ivp": None
        }

        try:
            # We want lookback period up to today
            min_date = dates[0]
            max_date = dates[-1]
            hist_iv_query = text("""
                SELECT trade_date, atm_iv
                FROM historical_atm_iv
                WHERE symbol = :symbol
                  AND trade_date >= :min_date AND trade_date <= :max_date
                ORDER BY trade_date ASC
            """)
            hist_iv_result = db.execute(hist_iv_query, {"symbol": symbol, "min_date": min_date, "max_date": max_date}).fetchall()

            if hist_iv_result:
                iv_series = [float(r[1]) for r in hist_iv_result if r[1] is not None]
                if iv_series:
                    min_iv = min(iv_series)
                    max_iv = max(iv_series)

                    # Use nearest expiry ATM IV as Current ATM IV for IVR/IVP
                    if cone_data["active_expiries"]:
                        current_atm_iv = cone_data["active_expiries"][0]["atm_iv"]
                        cone_data["iv_summary"]["current_atm_iv"] = current_atm_iv

                        if max_iv > min_iv:
                            ivr = (current_atm_iv - min_iv) / (max_iv - min_iv) * 100
                            cone_data["iv_summary"]["ivr"] = round(ivr, 2)

                        # IVP: Percentage of days where Historical_IV < Current_ATM_IV
                        days_below = sum(1 for iv in iv_series if iv < current_atm_iv)
                        ivp = (days_below / len(iv_series)) * 100
                        cone_data["iv_summary"]["ivp"] = round(ivp, 2)
        except Exception as e:
            print(f"Failed to calculate IVR/IVP: {e}")

        return cone_data
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/api/data/derivatives/pre_expiry_action/{symbol}")
def get_pre_expiry_action(
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
                    WHERE symbol = :symbol AND series = 'EQ'
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
        # Optimization: Only fetch where trade_date = expiry_date directly in SQL
        # This drastically reduces the number of rows scanned and joined.
        min_date = dates[0]
        max_date = dates[-1]

        expiry_query = text("""
            SELECT DISTINCT expiry_date
            FROM bhavcopy_fo
            WHERE ticker_symb = :symbol
              AND trade_date = expiry_date
              AND trade_date >= :min_date AND trade_date <= :max_date
              AND instrument_type IN ('FUTIDX', 'FUTSTK', 'STF', 'IDF')
        """)
        expiry_result = db.execute(expiry_query, {"symbol": symbol, "min_date": min_date, "max_date": max_date}).fetchall()

        expiries = set()
        for r in expiry_result:
            e_date = r[0].strftime('%Y-%m-%d')
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

        # Append ATM IV and India VIX overlay logic for the Pre-Expiry chart
        # This gives a single constant line across the chart for current values
        atm_iv_line = []
        india_vix_line = []
        try:
            # We fetch today's Cone endpoint to reuse the atm_iv and india_vix values
            cone_data = get_volatility_cone(symbol, lookback_days, False, db)
            atm_iv_val = cone_data.get("atm_iv", [None])[0]
            vix_val = cone_data.get("india_vix", [None])[0]
            atm_iv_line = [atm_iv_val] * len(dates)
            india_vix_line = [vix_val] * len(dates)
        except Exception as e:
            atm_iv_line = [None] * len(dates)
            india_vix_line = [None] * len(dates)

        # Precalculate price change percentages
        price_chg_pct_line = [0]
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                price_chg_pct_line.append(round(((prices[i] - prices[i-1]) / prices[i-1]) * 100, 2))
            else:
                price_chg_pct_line.append(0)

        return {
            "dates": dates,
            "prices": prices,
            "rv": rv_line,
            "expiries": sorted_expiries,
            "boxes": boxes,
            "atm_iv_line": atm_iv_line,
            "india_vix_line": india_vix_line,
            "price_chg_pct_line": price_chg_pct_line
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
