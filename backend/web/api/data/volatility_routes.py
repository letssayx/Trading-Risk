from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.infrastructure.db import get_db
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
        fetch_limit = lookback_days + 50

        # Need OHLC for Yang-Zhang
        if is_index:
            query = text("""
                SELECT trade_date, open_price, high_price, low_price, close_price
                FROM historical_index_data
                WHERE index_name = :symbol
                ORDER BY trade_date DESC
                LIMIT :lookback
            """)
        else:
            query = text("""
                SELECT trade_date, open_price, high_price, low_price, close_price
                FROM bhavcopy_eq
                WHERE ticker_symb = :symbol AND series = 'EQ'
                ORDER BY trade_date DESC
                LIMIT :lookback
            """)

        result = db.execute(query, {"symbol": symbol, "lookback": fetch_limit}).fetchall()

        # fallback to futures if eq/index is empty
        if not result:
             try:
                 query = text("""
                    SELECT * FROM (
                        SELECT DISTINCT ON (trade_date) trade_date, open_price, high_price, low_price, close_price
                        FROM bhavcopy_fo
                        WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK', 'IDF', 'STF')
                        ORDER BY trade_date DESC, expiry_date ASC
                    ) AS distinct_dates
                    ORDER BY trade_date DESC
                    LIMIT :lookback
                """)
                 result = db.execute(query, {"symbol": symbol, "lookback": fetch_limit}).fetchall()
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

        ohlc_result = db.execute(ohlc_query, {"symbol": symbol, "lookback": fetch_limit}).fetchall()

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
                 ohlc_result = db.execute(ohlc_query, {"symbol": symbol, "lookback": fetch_limit}).fetchall()
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
        import pandas as pd

        df = pd.DataFrame(ohlc_result, columns=["date", "open", "high", "low", "close"])
        df = df.sort_values("date")

        opens = df["open"].astype(float)
        highs = df["high"].astype(float)
        lows  = df["low"].astype(float)
        closes= df["close"].astype(float)

        opens = opens.mask(opens == 0, closes)
        highs = highs.mask(highs == 0, closes)
        lows  = lows.mask(lows == 0, closes)

        # Step 1: Overnight variance (previous close to today's open)
        prev_closes = closes.shift(1)
        overnight_ret = np.log(opens / prev_closes)
        overnight_var = overnight_ret ** 2

        # Step 2: Daytime Garman-Klass variance
        log_hl = np.log(highs / lows)
        log_co = np.log(closes / opens)
        daytime_var = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1) * (log_co ** 2)
        daytime_var = daytime_var.clip(lower=0)

        # Step 3: Yang-Zhang combination (weighted)
        # For daily data, overnight and daytime have equal weight in variance terms
        total_var = overnight_var + daytime_var

        # Step 4: Remove outliers (99.5th percentile)
        limit = np.percentile(total_var.dropna(), 99.5)
        total_var = total_var.clip(upper=limit)

        # Calculate rolling volatilities for ALL windows first
        rolling_vols = {}

        for w in windows:
            rolling_mean_var = total_var.rolling(window=w).mean()
            rolling_vol = np.sqrt(rolling_mean_var * 252) * 100
            rolling_vols[w] = rolling_vol

        # Create DataFrame with all windows
        vol_df = pd.DataFrame(rolling_vols)

        # CRITICAL FIX: Drop rows where ANY window has NaN
        # This ensures all windows use the EXACT same dates
        vol_df = vol_df.dropna()

        # Now calculate percentiles from the aligned data
        for i, w in enumerate(windows):
            valid_vol = vol_df[w].tail(lookback_days)

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
                # Skip expiries that are too close (noise)
                if current_dte < 3: continue

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

                    # Map DTE to closest rolling window for comparison overlay
                    mapped_n = None
                    if 1 <= current_dte <= 3:
                        mapped_n = min([1, 2, 3], key=lambda x: abs(x - current_dte))
                    elif 5 <= current_dte <= 10:
                        mapped_n = min([5, 10], key=lambda x: abs(x - current_dte))
                    elif 15 <= current_dte <= 30:
                        mapped_n = min([21, 30], key=lambda x: abs(x - current_dte))

                    active_expiries.append({
                        "expiry_date": exp_d.strftime('%Y-%m-%d'),
                        "dte": current_dte,
                        "mapped_n": mapped_n,
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
            # Fetch India VIX for overlay if requested
            vix_query = text("""
                SELECT close_price
                FROM historical_index_data
                WHERE index_name = 'INDIA VIX' AND trade_date = :current_date
            """)
            vix_result = db.execute(vix_query, {"current_date": current_date}).fetchone()
            if vix_result:
                cone_data["india_vix"] = [float(vix_result[0])]
        except Exception:
            pass

        try:
            # We want lookback period up to today
            # If the user has just clicked run, they may have backfilled history up to today
            # But "active_expiries" comes from today's live options chain or latest EOD, so current ATM IV might differ slightly from the backfilled historic value if it wasn't backfilled today
            # We should use the precalculated historic IV's latest value as "Current ATM IV" for consistency, or the nearest expiry from "active_expiries"
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

                        # Add ATM IV to top level dict for other routes to use
                        cone_data["atm_iv"] = [current_atm_iv]

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
        is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

        try:
            if is_index:
                idx_query = text("""
                    SELECT trade_date, open_price, high_price, low_price, close_price
                    FROM historical_index_data
                    WHERE index_name = :symbol
                    ORDER BY trade_date DESC
                    LIMIT :lookback
                """)
                result = db.execute(idx_query, {"symbol": symbol, "lookback": lookback_days}).fetchall()
            else:
                query = text("""
                    SELECT trade_date, open_price, high_price, low_price, close_price
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
                        SELECT DISTINCT ON (trade_date) trade_date, open_price, high_price, low_price, close_price
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
        prices = [float(r[4]) for r in result]  # index 4 is close_price

        # Calculate Rolling Realized Volatility for the box_days window using Yang-Zhang
        rv_line = [None] * len(dates)

        import pandas as pd
        df = pd.DataFrame(result, columns=["date", "open", "high", "low", "close"])
        df = df.sort_values("date")

        opens = df["open"].astype(float)
        highs = df["high"].astype(float)
        lows  = df["low"].astype(float)
        closes= df["close"].astype(float)

        opens = opens.mask(opens == 0, closes)
        highs = highs.mask(highs == 0, closes)
        lows  = lows.mask(lows == 0, closes)

        prev_closes = closes.shift(1)
        overnight_ret = np.log(opens / prev_closes)
        overnight_var = overnight_ret ** 2

        log_hl = np.log(highs / lows)
        log_co = np.log(closes / opens)
        daytime_var = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1) * (log_co ** 2)
        daytime_var = daytime_var.clip(lower=0)

        total_var = overnight_var + daytime_var
        limit = np.percentile(total_var.dropna(), 99.5)
        total_var = total_var.clip(upper=limit)

        rolling_mean_var = pd.Series(total_var).rolling(window=box_days).mean()
        rolling_mean_var = rolling_mean_var.clip(lower=0)

        rolling_vol_annualized = np.sqrt(rolling_mean_var * 252) * 100

        for i in range(len(rolling_vol_annualized)):
            val = rolling_vol_annualized.iloc[i]
            if not np.isnan(val):
                rv_line[i] = round(float(val), 2)

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

        # Append ATM IV overlay logic for the Pre-Expiry chart
        # User requested 1 moving point for today's date only
        atm_iv_line = [None] * len(dates)
        try:
            cone_data = get_volatility_cone(symbol, lookback_days, False, db)
            atm_iv_val = cone_data.get("atm_iv", [None])[0]
            if atm_iv_val is not None:
                atm_iv_line[-1] = atm_iv_val  # Plot only on the last day (today)
        except Exception:
            pass

        # Fetch actual historical India VIX for the exact dates
        india_vix_line = [None] * len(dates)
        try:
            vix_query = text("""
                SELECT trade_date, close_price
                FROM historical_index_data
                WHERE index_name = 'INDIA VIX'
                  AND trade_date >= :min_date
                  AND trade_date <= :max_date
            """)
            vix_result = db.execute(vix_query, {"min_date": dates[0], "max_date": dates[-1]}).fetchall()
            vix_dict = {r[0].strftime('%Y-%m-%d'): float(r[1]) for r in vix_result}

            for i, d in enumerate(dates):
                india_vix_line[i] = vix_dict.get(d, None)
        except Exception:
            pass

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

@router.get("/api/data/derivatives/volatility_summary_all")
def get_volatility_summary_all(db: Session = Depends(get_db), expiry_type: str = Query("monthly", description="monthly or all")):
    try:
        from backend.ingest.nse_models import VolatilityAnalysisMetrics, BhavcopyEQ, HistoricalIndexData
        from sqlalchemy import func

        latest_date = db.query(func.max(VolatilityAnalysisMetrics.trade_date)).scalar()
        if not latest_date:
            return {"data": []}

        metrics = db.query(VolatilityAnalysisMetrics).filter(VolatilityAnalysisMetrics.trade_date == latest_date).all()

        # Need latest prices from EQ and FO/Indices
        eq_records = db.query(
            BhavcopyEQ.symbol, BhavcopyEQ.close_price
        ).filter(BhavcopyEQ.trade_date == latest_date, BhavcopyEQ.series == 'EQ').all()

        idx_records = db.query(
            HistoricalIndexData.index_name, HistoricalIndexData.close_price
        ).filter(HistoricalIndexData.trade_date == latest_date).all()

        price_map = {}
        for r in eq_records:
            price_map[r.symbol] = r.close_price
        for r in idx_records:
            price_map[r.index_name] = r.close_price

        data = []
        for m in metrics:
            data.append({
                "symbol": m.symbol,
                "price": round(price_map.get(m.symbol, 0), 2),
                "current_atm_iv": round(m.current_iv, 2) if m.current_iv is not None else None,
                "ivr": round(m.ivr, 2) if m.ivr is not None else None,
                "ivp": round(m.ivp, 2) if m.ivp is not None else None
            })

        return {"data": data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/data/analysis/volatility/sync")
def sync_volatility_analysis(force: str = "false", db: Session = Depends(get_db)):
    try:
        from backend.ingest.nse_models import BhavcopyFO, VolatilityAnalysisMetrics
        from sqlalchemy import func

        latest_raw_date = db.query(func.max(BhavcopyFO.trade_date)).filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).scalar()
        latest_metric_date = db.query(func.max(VolatilityAnalysisMetrics.trade_date)).scalar()

        if latest_raw_date and latest_metric_date and latest_raw_date <= latest_metric_date and force.lower() != "true":
            return {"status": "success", "message": "Data is already up to date.", "computed": False, "latest_date": str(latest_raw_date)}

        compute_lookback = None if force.lower() == "true" else (str(latest_metric_date) if latest_metric_date else None)
        return compute_volatility_analysis(db, latest_metric_date=compute_lookback)
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.post("/api/data/analysis/volatility/compute")
def compute_volatility_analysis(db: Session = Depends(get_db), latest_metric_date: str = None):
    try:
        from backend.ingest.nse_models import BhavcopyFO, HistoricalATMIV, VolatilityAnalysisMetrics
        from sqlalchemy.dialects.postgresql import insert
        import datetime

        latest_metric_date_obj = datetime.datetime.strptime(latest_metric_date, "%Y-%m-%d").date() if latest_metric_date else None

        all_dates_query = db.query(BhavcopyFO.trade_date).filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).distinct().order_by(BhavcopyFO.trade_date.desc()).all()
        all_dates = [d[0] for d in all_dates_query]

        if not all_dates:
            return {"status": "error", "message": "No data found."}

        dates_to_compute = []
        if latest_metric_date_obj:
            dates_to_compute = [d for d in all_dates if d > latest_metric_date_obj]
        else:
            dates_to_compute = all_dates[:32]

        if not dates_to_compute:
            return {"status": "success", "message": "No new dates to compute.", "computed": False}

        iv_records = db.query(
            HistoricalATMIV.trade_date, HistoricalATMIV.symbol, HistoricalATMIV.atm_iv
        ).filter(HistoricalATMIV.trade_date.in_(dates_to_compute)).all()

        # Need historic data up to max lookback (252) to compute IVP/IVR for each date
        hist_dates_query = db.query(BhavcopyFO.trade_date).filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).distinct().order_by(BhavcopyFO.trade_date.desc()).limit(252).all()
        hist_dates = [d[0] for d in hist_dates_query]

        all_hist_ivs = db.query(
            HistoricalATMIV.trade_date, HistoricalATMIV.symbol, HistoricalATMIV.atm_iv
        ).filter(HistoricalATMIV.trade_date.in_(hist_dates)).all()

        hist_iv_map = {}
        for r in all_hist_ivs:
            if r.symbol not in hist_iv_map:
                hist_iv_map[r.symbol] = {}
            hist_iv_map[r.symbol][r.trade_date] = float(r.atm_iv) if r.atm_iv is not None else 0.0

        metrics = []
        for r in iv_records:
            iv = float(r.atm_iv) if r.atm_iv else 0.0
            sym = r.symbol
            dt = r.trade_date

            ivp = 0.0
            ivr = 0.0

            # Calculate IVP / IVR looking back from 'dt'
            if sym in hist_iv_map:
                past_ivs = [v for d, v in hist_iv_map[sym].items() if d <= dt]
                if past_ivs:
                    min_iv = min(past_ivs)
                    max_iv = max(past_ivs)
                    if max_iv > min_iv:
                        ivr = ((iv - min_iv) / (max_iv - min_iv)) * 100

                    days_below = sum(1 for v in past_ivs if v < iv)
                    ivp = (days_below / len(past_ivs)) * 100

            interp = "Neutral"
            if iv > 25 and ivp > 80: interp = "Extremely High Volatility"
            elif ivp > 70: interp = "High Volatility"
            elif ivp < 20: interp = "Low Volatility"

            metrics.append({
                "trade_date": dt,
                "symbol": sym,
                "current_iv": iv,
                "iv_chg_pct": 0.0,
                "ivp": ivp,
                "ivr": ivr,
                "rv_1mo": 0.0,
                "rv_3mo": 0.0,
                "rv_12mo": 0.0,
                "iv_rv_spread": 0.0,
                "price": 0.0,
                "price_chg_pct": 0.0
            })

        if metrics:
            stmt = insert(VolatilityAnalysisMetrics).values(metrics)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_volatility_analysis_metrics_date_symbol',
                set_={
                    'current_iv': stmt.excluded.current_iv,
                    'iv_chg_pct': stmt.excluded.iv_chg_pct,
                    'ivp': stmt.excluded.ivp,
                    'ivr': stmt.excluded.ivr,
                    'rv_1mo': stmt.excluded.rv_1mo,
                    'rv_3mo': stmt.excluded.rv_3mo,
                    'rv_12mo': stmt.excluded.rv_12mo,
                    'iv_rv_spread': stmt.excluded.iv_rv_spread,
                    'price': stmt.excluded.price,
                    'price_chg_pct': stmt.excluded.price_chg_pct
                }
            )
            db.execute(stmt)
            db.commit()

        return {"status": "success", "message": f"Computed {len(metrics)} records for {len(dates_to_compute)} dates.", "computed": True}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}
