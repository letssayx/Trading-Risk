from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.infrastructure.db import get_db
import numpy as np

router = APIRouter()

# Vectorized Black-Scholes Delta
def calc_bs_delta_vectorized(S, K, T, r, sigma, is_call):
    """
    S: Array of spot prices
    K: Array of strike prices
    T: Array of time to expiration (in years)
    r: Float (risk-free rate)
    sigma: Float or Array (volatility)
    is_call: Boolean or Array of Booleans
    """
    # Protect against T=0 or zero volatility
    T = np.maximum(T, 1e-5)
    sigma = np.maximum(sigma, 1e-5)

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    # Fast vectorized normal CDF approximation
    import math
    def norm_cdf(x):
        return (1.0 + np.vectorize(math.erf)(x / np.sqrt(2.0))) / 2.0

    delta = norm_cdf(d1)

    # If not call, subtract 1
    return np.where(is_call, delta, delta - 1.0)

@router.get("/api/data/derivatives/pcr_history")
def get_pcr_history(symbol: str, days: int = 500, expiry_only: bool = False, db: Session = Depends(get_db)):
    try:
        from backend.ingest.nse_models import OiAnalysisMetrics
        from sqlalchemy import desc

        symbol = symbol.upper()

        import datetime
        today_date = datetime.date.today()

        if expiry_only:
            # Get expiry dates
            expiries_query = text("""
                SELECT DISTINCT expiry_date
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
            """)
            expiries_result = db.execute(expiries_query, {"symbol": symbol}).fetchall()
            valid_dates = [r[0] for r in expiries_result]

            if not valid_dates:
                return {"dates": [], "price": [], "ce_oi": [], "pe_oi": [], "total_oi": [], "pcr": []}

            query = db.query(OiAnalysisMetrics).filter(
                OiAnalysisMetrics.symbol == symbol,
                OiAnalysisMetrics.trade_date.in_(valid_dates),
                OiAnalysisMetrics.trade_date <= today_date
            ).order_by(desc(OiAnalysisMetrics.trade_date)).limit(days).all()
        else:
            query = db.query(OiAnalysisMetrics).filter(
                OiAnalysisMetrics.symbol == symbol,
                OiAnalysisMetrics.trade_date <= today_date
            ).order_by(desc(OiAnalysisMetrics.trade_date)).limit(int(days)).all()



        # Reverse to get chronological order (oldest to newest) for chart
        query = query[::-1]

        result_dates = []
        result_prices = []
        result_ce_oi = []
        result_pe_oi = []
        result_total_oi = []
        result_fut_oi = []
        result_pcr = []

        for r in query:
            result_dates.append(r.trade_date.strftime('%Y-%m-%d'))
            result_prices.append(float(r.price) if r.price else 0.0)
            result_ce_oi.append(int(r.call_oi) if r.call_oi else 0)
            result_pe_oi.append(int(r.put_oi) if r.put_oi else 0)
            result_total_oi.append(int(r.total_oi) if r.total_oi else 0)
            result_fut_oi.append(int(r.fut_oi) if r.fut_oi else 0)
            result_pcr.append(float(r.pcr) if r.pcr else 0.0)

        return {
            "dates": result_dates,
            "price": result_prices,
            "ce_oi": result_ce_oi,
            "pe_oi": result_pe_oi,
            "total_oi": result_total_oi,
            "fut_oi": result_fut_oi,
            "pcr": result_pcr
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/data/derivatives/covered_call_backtest")
def get_covered_call_backtest(
    symbol: str,
    start_date: str,
    end_date: str,
    call_strike_pct: float = 4.0,
    put_strike_pct: float = 0.0,
    use_collar: bool = False,
    hold_stock_continuously: bool = False,
    db: Session = Depends(get_db)
):
    """
    Backtests a covered call (and optional collar) strategy on historical EOD data.
    - call_strike_pct: 4.0 means 4% OTM. -5.0 means 5% ITM.
    - put_strike_pct: 0.0 means ATM, -5.0 means 5% OTM.
    """
    try:
        from backend.ingest.nse_models import BhavcopyFO, BhavcopyEQ, HistoricalIndexData, HistoricalATMIV
        from sqlalchemy import asc, desc
        import datetime
        import math

        symbol = symbol.upper()
        is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

        # Parse dates
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        # 1. Get all monthly expiry dates in the date range.
        # We define a monthly expiry as the last expiry date of the month.
        expiries_query = text("""
            WITH Expiries AS (
                SELECT DISTINCT expiry_date,
                       EXTRACT(YEAR FROM expiry_date) as exp_year,
                       EXTRACT(MONTH FROM expiry_date) as exp_month
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND trade_date BETWEEN :start AND :end
            ),
            MonthlyExpiries AS (
                SELECT exp_year, exp_month, MAX(expiry_date) as monthly_expiry
                FROM Expiries
                GROUP BY exp_year, exp_month
            )
            SELECT monthly_expiry FROM MonthlyExpiries ORDER BY monthly_expiry ASC
        """)

        result = db.execute(expiries_query, {"symbol": symbol, "start": start_dt, "end": end_dt}).fetchall()
        monthly_expiries = [r[0] for r in result]

        if not monthly_expiries:
            return {"status": "error", "message": "No expiries found in this date range."}

        # Find all trading dates for this symbol in range to define cycle start/end
        if is_index:
            trading_dates_query = text("""
                SELECT trade_date, close_price FROM historical_index_data
                WHERE index_name = :symbol AND trade_date BETWEEN :start AND :end
                ORDER BY trade_date ASC
            """)
        else:
            trading_dates_query = text("""
                SELECT trade_date, close_price FROM bhavcopy_eq
                WHERE symbol = :symbol AND series = 'EQ' AND trade_date BETWEEN :start AND :end
                ORDER BY trade_date ASC
            """)

        td_result = db.execute(trading_dates_query, {"symbol": symbol, "start": start_dt, "end": end_dt}).fetchall()
        trading_dates = [r[0] for r in td_result]
        spot_prices = {r[0]: float(r[1]) for r in td_result}

        cycles = []
        daily_mtm = []

        # We will loop through each expiry.
        # The cycle starts on the first trading day after the PREVIOUS expiry (or start_date for the first one).
        initial_entry_spot = None

        for i, expiry in enumerate(monthly_expiries):
            if i == 0:
                # Find the first trading date in our dataset that is <= expiry
                possible_starts = [d for d in trading_dates if d <= expiry]
                if not possible_starts: continue
                cycle_start = possible_starts[0]
            else:
                prev_expiry = monthly_expiries[i-1]
                possible_starts = [d for d in trading_dates if d > prev_expiry and d <= expiry]
                if not possible_starts: continue
                cycle_start = possible_starts[0]

            if cycle_start not in spot_prices:
                continue

            # Entry spot for options calculation is ALWAYS the cycle_start spot
            cycle_entry_spot = spot_prices[cycle_start]

            # Stock entry spot depends on continuous holding flag
            if hold_stock_continuously:
                if initial_entry_spot is None:
                    initial_entry_spot = cycle_entry_spot
                stock_entry_spot = initial_entry_spot
            else:
                stock_entry_spot = cycle_entry_spot

            entry_spot = cycle_entry_spot # for legacy variables, option targets use this

            # Calculate target strikes
            target_call_strike = entry_spot * (1 + (call_strike_pct / 100.0))
            target_put_strike = entry_spot * (1 + (put_strike_pct / 100.0))

            # Fetch available options on the cycle start date for this expiry
            opt_query = text("""
                SELECT strike_price, option_type, close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND trade_date = :trade_date
                  AND expiry_date = :expiry
            """)
            opt_res = db.execute(opt_query, {"symbol": symbol, "trade_date": cycle_start, "expiry": expiry}).fetchall()

            if not opt_res:
                continue

            calls = [r for r in opt_res if r[1] == 'CE']
            puts = [r for r in opt_res if r[1] == 'PE']

            if not calls:
                continue

            # Find closest call strike
            closest_call = min(calls, key=lambda x: abs(x[0] - target_call_strike))
            call_strike = closest_call[0]
            call_entry_price = float(closest_call[2])

            put_strike = None
            put_entry_price = 0.0
            closest_put = None
            if use_collar and puts:
                closest_put = min(puts, key=lambda x: abs(x[0] - target_put_strike))
                put_strike = closest_put[0]
                put_entry_price = float(closest_put[2])

            # Calculate expected move (Implied Move) formulas on entry day
            # 1. Volatility Implied Move: Annualized Vol * Sqrt(t/252)
            days_to_expiry = (expiry - cycle_start).days
            trading_days_to_expiry = len([d for d in trading_dates if cycle_start <= d <= expiry])

            iv_query = text("""
                SELECT atm_iv FROM historical_atm_iv
                WHERE symbol = :symbol AND trade_date = :trade_date
            """)
            iv_res = db.execute(iv_query, {"symbol": symbol, "trade_date": cycle_start}).first()
            atm_iv = float(iv_res[0]) if iv_res and iv_res[0] else 20.0 # Default 20% if missing

            implied_move_vol = (atm_iv / 100.0) * math.sqrt(trading_days_to_expiry / 252.0)

            # 2. Empirically derived: 85% * ATM Straddle
            atm_strike = min(calls, key=lambda x: abs(x[0] - entry_spot))[0]
            atm_call = next((r for r in calls if r[0] == atm_strike), None)
            atm_put = next((r for r in puts if r[0] == atm_strike), None)

            straddle_price = 0
            if atm_call and atm_put:
                straddle_price = float(atm_call[2]) + float(atm_put[2])

            implied_move_empirical = 0.85 * (straddle_price / entry_spot) if entry_spot > 0 else 0

            # Fetch daily data for this cycle to build MTM
            daily_opts_query = text("""
                SELECT trade_date, strike_price, option_type, close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND trade_date >= :start_date AND trade_date <= :expiry
                  AND expiry_date = :expiry
                  AND strike_price IN :strikes
            """)
            # using a tuple for strikes
            strikes = tuple(set([call_strike, put_strike, atm_strike] + ([put_strike] if put_strike else [])))
            # Handle tuple size 1 syntax for IN clause
            if len(strikes) == 1:
                strikes = (strikes[0], strikes[0])

            d_opts_res = db.execute(daily_opts_query, {
                "symbol": symbol,
                "start_date": cycle_start,
                "expiry": expiry,
                "strikes": strikes
            }).fetchall()

            daily_opts = {}
            for r in d_opts_res:
                dt = r[0]
                stk = r[1]
                typ = r[2]
                prc = float(r[3])
                if dt not in daily_opts:
                    daily_opts[dt] = {}
                daily_opts[dt][(stk, typ)] = prc

            cycle_mtm = []
            final_pnl = 0
            for dt in [d for d in trading_dates if cycle_start <= d <= expiry]:
                if dt not in spot_prices: continue
                current_spot = spot_prices[dt]

                # Stock PnL
                stock_pnl = current_spot - stock_entry_spot

                # Call PnL (Short Call)
                call_prc = daily_opts.get(dt, {}).get((call_strike, 'CE'), call_entry_price)
                if dt == expiry:
                    # Intrinsic value at expiry
                    call_prc = max(0, current_spot - call_strike)
                call_pnl = call_entry_price - call_prc

                # Put PnL (Long Put)
                put_pnl = 0
                if use_collar and put_strike:
                    put_prc = daily_opts.get(dt, {}).get((put_strike, 'PE'), put_entry_price)
                    if dt == expiry:
                        put_prc = max(0, put_strike - current_spot)
                    put_pnl = put_prc - put_entry_price

                total_pnl = stock_pnl + call_pnl + put_pnl
                total_pnl_pct = (total_pnl / entry_spot) * 100

                cycle_mtm.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "spot": current_spot,
                    "call_price": call_prc,
                    "put_price": put_prc if use_collar else 0,
                    "total_pnl": total_pnl,
                    "total_pnl_pct": total_pnl_pct
                })

                daily_mtm.append({
                    "expiry_cycle": expiry.strftime("%Y-%m-%d"),
                    "date": dt.strftime("%Y-%m-%d"),
                    "spot": current_spot,
                    "stock_pnl": stock_pnl,
                    "call_pnl": call_pnl,
                    "put_pnl": put_pnl,
                    "total_pnl": total_pnl,
                    "total_pnl_pct": total_pnl_pct
                })

                if dt == expiry:
                    final_pnl = total_pnl
                    final_pnl_pct = total_pnl_pct

            expiry_spot = spot_prices.get(expiry, current_spot)

            # Max profit for covered call = (Call Strike - Stock Entry Spot) + Call Premium
            max_profit = (call_strike - stock_entry_spot) + call_entry_price
            if use_collar and put_strike:
                max_profit -= put_entry_price

            max_loss = stock_entry_spot - call_entry_price
            if use_collar and put_strike:
                max_loss = stock_entry_spot - put_strike - call_entry_price + put_entry_price

            # Actual move is based on the stock entry price logic
            actual_move_pct = ((expiry_spot - stock_entry_spot) / stock_entry_spot) * 100

            cycles.append({
                "actual_move_pct": actual_move_pct,
                "expiry": expiry.strftime("%Y-%m-%d"),
                "entry_date": cycle_start.strftime("%Y-%m-%d"),
                "entry_spot": cycle_entry_spot,
                "expiry_spot": expiry_spot,
                "call_strike": call_strike,
                "call_premium": call_entry_price,
                "put_strike": put_strike,
                "put_premium": put_entry_price,
                "implied_move_vol_pct": implied_move_vol * 100,
                "implied_move_emp_pct": implied_move_empirical * 100,
                "atm_iv": atm_iv,
                "max_profit": max_profit,
                "max_profit_pct": (max_profit / entry_spot) * 100,
                "max_loss": max_loss,
                "max_loss_pct": (max_loss / entry_spot) * 100,
                "final_pnl": final_pnl,
                "final_pnl_pct": final_pnl_pct
            })

        return {
            "status": "success",
            "symbol": symbol,
            "cycles": cycles,
            "daily_mtm": daily_mtm
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.get("/api/data/derivatives/binomial_paths")
def get_binomial_paths(symbol: str, expiry_date: str = None, custom_iv: float = None, lookback_days: int = 500, db: Session = Depends(get_db)):
    """
    Generates probability paths (1 SD, 2 SD) from the current spot price to expiry based on current IV.
    Used for overlaying a predictive 'cone' on the UI chart.
    """
    try:
        from backend.ingest.nse_models import BhavcopyFO, HistoricalATMIV, BhavcopyEQ, HistoricalIndexData
        import datetime
        import math

        symbol = symbol.upper()
        is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

        # Fetch latest spot
        if is_index:
            latest_spot_query = text("SELECT trade_date, close_price FROM historical_index_data WHERE index_name = :symbol ORDER BY trade_date DESC LIMIT 1")
        else:
            latest_spot_query = text("SELECT trade_date, close_price FROM bhavcopy_eq WHERE symbol = :symbol AND series = 'EQ' ORDER BY trade_date DESC LIMIT 1")

        spot_res = db.execute(latest_spot_query, {"symbol": symbol}).first()
        if not spot_res:
            return {"status": "error", "message": "No spot price found."}

        current_date, current_spot = spot_res[0], float(spot_res[1])

        # Get target expiry
        if expiry_date:
            target_expiry = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
        else:
            exp_query = text("SELECT MIN(expiry_date) FROM bhavcopy_fo WHERE ticker_symb = :symbol AND expiry_date >= :dt")
            exp_res = db.execute(exp_query, {"symbol": symbol, "dt": current_date}).first()
            if not exp_res or not exp_res[0]:
                return {"status": "error", "message": "No future expiries found."}
            target_expiry = exp_res[0]

        days_to_expiry = (target_expiry - current_date).days
        if days_to_expiry < 0:
            return {"status": "error", "message": "Expiry date is in the past."}

        # Get ATM IV or use Custom IV
        if custom_iv is not None and custom_iv > 0:
            atm_iv = custom_iv / 100.0
        else:
            iv_query = text("SELECT atm_iv FROM historical_atm_iv WHERE symbol = :symbol AND trade_date <= :dt ORDER BY trade_date DESC LIMIT 1")
            iv_res = db.execute(iv_query, {"symbol": symbol, "dt": current_date}).first()
            atm_iv = float(iv_res[0]) / 100.0 if iv_res and iv_res[0] else 0.20 # default 20%

        # Calculate Current Implied Moves for today
        trading_days_to_expiry = len([d for d in [current_date + datetime.timedelta(days=x) for x in range(days_to_expiry+1)] if d.weekday() < 5])
        current_vol_implied_move = atm_iv * math.sqrt(trading_days_to_expiry / 252.0)

        # Try to calculate Empirical from straddle
        current_emp_implied_move = 0
        try:
            opt_query = text("""
                SELECT strike_price, option_type, close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND trade_date = :dt
                  AND expiry_date = :exp
            """)
            opt_res = db.execute(opt_query, {"symbol": symbol, "dt": current_date, "exp": target_expiry}).fetchall()
            if opt_res:
                calls = [r for r in opt_res if r[1] == 'CE']
                puts = [r for r in opt_res if r[1] == 'PE']
                if calls and puts:
                    atm_strike = min(calls, key=lambda x: abs(x[0] - current_spot))[0]
                    atm_call = next((r for r in calls if r[0] == atm_strike), None)
                    atm_put = next((r for r in puts if r[0] == atm_strike), None)
                    if atm_call and atm_put:
                        straddle_price = float(atm_call[2]) + float(atm_put[2])
                        current_emp_implied_move = 0.85 * (straddle_price / current_spot)
        except Exception as straddle_e:
            pass

        # Generate paths
        # We'll generate daily SD lines up to expiry
        paths = []
        for i in range(days_to_expiry + 1):
            target_dt = current_date + datetime.timedelta(days=i)
            # Calculate standard deviation range for 'i' days
            # SD = Spot * Vol * Sqrt(t/365)
            sd_move = current_spot * atm_iv * math.sqrt(i / 365.0)

            paths.append({
                "date": target_dt.strftime("%Y-%m-%d"),
                "days_out": i,
                "spot_ref": current_spot,
                "sd_1_up": current_spot + sd_move,
                "sd_1_down": current_spot - sd_move,
                "sd_2_up": current_spot + (2 * sd_move),
                "sd_2_down": current_spot - (2 * sd_move)
            })

        return {
            "status": "success",
            "symbol": symbol,
            "current_date": current_date.strftime("%Y-%m-%d"),
            "expiry_date": target_expiry.strftime("%Y-%m-%d"),
            "current_spot": current_spot,
            "current_iv": atm_iv * 100,
            "current_vol_implied_move_pct": current_vol_implied_move * 100,
            "current_emp_implied_move_pct": current_emp_implied_move * 100,
            "paths": paths
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.get("/api/data/derivatives/covered_call_all_fo_export")
def get_covered_call_all_fo_export(
    start_date: str,
    end_date: str,
    call_strike_pct: float = 4.0,
    put_strike_pct: float = 0.0,
    use_collar: bool = False,
    hold_stock_continuously: bool = False,
    db: Session = Depends(get_db)
):
    """
    Highly optimized bulk export of covered call / collar strategy for ALL F&O stocks.
    Generates a cycle-by-cycle summary for every valid F&O stock and streams as XLSX.
    """
    try:
        import pandas as pd
        import io
        import datetime
        from fastapi.responses import StreamingResponse
        from sqlalchemy import text
        from backend.ingest.nse_models import BhavcopyFO, BhavcopyEQ

        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        # 1. Get all monthly expiries for ALL F&O symbols within range
        exp_query = text("""
            WITH Expiries AS (
                SELECT DISTINCT ticker_symb, expiry_date,
                       EXTRACT(YEAR FROM expiry_date) as exp_year,
                       EXTRACT(MONTH FROM expiry_date) as exp_month
                FROM bhavcopy_fo
                WHERE instrument_type IN ('OPTSTK', 'OPTIDX')
                  AND trade_date BETWEEN :start AND :end
            ),
            MonthlyExpiries AS (
                SELECT ticker_symb, exp_year, exp_month, MAX(expiry_date) as monthly_expiry
                FROM Expiries
                GROUP BY ticker_symb, exp_year, exp_month
            )
            SELECT ticker_symb, monthly_expiry FROM MonthlyExpiries ORDER BY ticker_symb, monthly_expiry ASC
        """)
        exp_res = db.execute(exp_query, {"start": start_dt, "end": end_dt}).fetchall()

        # Group expiries by symbol
        sym_expiries = {}
        for r in exp_res:
            sym, exp = r[0], r[1]
            if sym not in sym_expiries:
                sym_expiries[sym] = []
            sym_expiries[sym].append(exp)

        # 2. Get all trading dates for all symbols to define cycle starts
        # We need equity spots. For indices, we need index spots.
        eq_dates_query = text("""
            SELECT symbol, trade_date, close_price
            FROM bhavcopy_eq
            WHERE series = 'EQ' AND trade_date BETWEEN :start AND :end
        """)
        eq_res = db.execute(eq_dates_query, {"start": start_dt, "end": end_dt}).fetchall()

        idx_dates_query = text("""
            SELECT index_name, trade_date, close_price
            FROM historical_index_data
            WHERE trade_date BETWEEN :start AND :end
        """)
        idx_res = db.execute(idx_dates_query, {"start": start_dt, "end": end_dt}).fetchall()

        # Build massive spot map: spot_map[symbol][date] = price
        spot_map = {}
        for r in eq_res:
            sym, dt, prc = r[0], r[1], float(r[2])
            if sym not in spot_map: spot_map[sym] = {}
            spot_map[sym][dt] = prc

        for r in idx_res:
            sym, dt, prc = r[0], r[1], float(r[2])
            if sym not in spot_map: spot_map[sym] = {}
            spot_map[sym][dt] = prc

        # Get all distinct trading dates generally (to find first available day for indices/stocks)
        all_dates_query = text("SELECT DISTINCT trade_date FROM bhavcopy_eq WHERE trade_date BETWEEN :start AND :end ORDER BY trade_date ASC")
        all_dates = [r[0] for r in db.execute(all_dates_query, {"start": start_dt, "end": end_dt}).fetchall()]

        # 3. Identify Entry Dates and Expiry Dates for all cycles
        cycle_targets = []  # List of tuples: (symbol, cycle_start, expiry)

        for sym, expiries in sym_expiries.items():
            if sym not in spot_map:
                continue # Skip if no spot data at all

            sym_dates = sorted(spot_map[sym].keys())
            if not sym_dates: continue

            for i, expiry in enumerate(expiries):
                if i == 0:
                    possible_starts = [d for d in sym_dates if d <= expiry]
                    if not possible_starts: continue
                    cycle_start = possible_starts[0]
                else:
                    prev_expiry = expiries[i-1]
                    possible_starts = [d for d in sym_dates if d > prev_expiry and d <= expiry]
                    if not possible_starts: continue
                    cycle_start = possible_starts[0]

                cycle_targets.append((sym, cycle_start, expiry))

        if not cycle_targets:
            raise Exception("No valid cycles found for any F&O symbol.")

        # 4. Fetch all necessary option data in bulk
        # To avoid massive memory explosion, we'll query options only on cycle_start and expiry dates
        target_option_dates = list(set([c[1] for c in cycle_targets] + [c[2] for c in cycle_targets]))

        # Batch option fetching to avoid huge IN clauses
        chunk_size = 50
        all_opts = []
        for i in range(0, len(target_option_dates), chunk_size):
            chunk_dates = target_option_dates[i:i+chunk_size]
            opts_q = text("""
                SELECT ticker_symb, trade_date, expiry_date, option_type, strike_price, close_price
                FROM bhavcopy_fo
                WHERE instrument_type IN ('OPTSTK', 'OPTIDX')
                  AND trade_date IN :dates
                  AND expiry_date IN :expiries
            """)
            # using target_option_dates as expiries as well to cover the span, though slightly wider than needed.
            # actually better to just filter on trade_date.
            opts_q2 = text("""
                SELECT ticker_symb, trade_date, expiry_date, option_type, strike_price, close_price
                FROM bhavcopy_fo
                WHERE instrument_type IN ('OPTSTK', 'OPTIDX')
                  AND trade_date IN :dates
            """)
            o_res = db.execute(opts_q2, {"dates": tuple(chunk_dates) if len(chunk_dates)>1 else (chunk_dates[0], chunk_dates[0])}).fetchall()
            all_opts.extend(o_res)

        # Build options map: opt_map[sym][trade_date][expiry][(type, strike)] = price
        opt_map = {}
        for r in all_opts:
            sym, dt, exp, typ, stk, prc = r[0], r[1], r[2], r[3], float(r[4]), float(r[5])
            if sym not in opt_map: opt_map[sym] = {}
            if dt not in opt_map[sym]: opt_map[sym][dt] = {}
            if exp not in opt_map[sym][dt]: opt_map[sym][dt][exp] = {}
            opt_map[sym][dt][exp][(typ, stk)] = prc

        # 5. Process cycles and build result rows
        results = []

        initial_spots = {}

        for sym, cycle_start, expiry in cycle_targets:
            cycle_entry_spot = spot_map[sym].get(cycle_start)
            expiry_spot = spot_map[sym].get(expiry)

            if cycle_entry_spot is None: continue

            if hold_stock_continuously:
                if sym not in initial_spots:
                    initial_spots[sym] = cycle_entry_spot
                stock_entry_spot = initial_spots[sym]
            else:
                stock_entry_spot = cycle_entry_spot

            entry_spot = cycle_entry_spot # target logic uses current cycle spot

            if entry_spot is None: continue

            target_call_strike = entry_spot * (1 + (call_strike_pct / 100.0))
            target_put_strike = entry_spot * (1 + (put_strike_pct / 100.0))

            available_opts = opt_map.get(sym, {}).get(cycle_start, {}).get(expiry, {})
            if not available_opts: continue

            calls = [(k[1], v) for k, v in available_opts.items() if k[0] == 'CE']
            puts = [(k[1], v) for k, v in available_opts.items() if k[0] == 'PE']

            if not calls: continue

            closest_call = min(calls, key=lambda x: abs(x[0] - target_call_strike))
            call_strike, call_entry_price = closest_call

            put_strike, put_entry_price = None, 0.0
            if use_collar and puts:
                closest_put = min(puts, key=lambda x: abs(x[0] - target_put_strike))
                put_strike, put_entry_price = closest_put

            # Evaluate final PnL at expiry
            # If no expiry spot (e.g. holiday mapping issue), skip cycle
            if expiry_spot is None: continue

            stock_pnl = expiry_spot - stock_entry_spot
            call_expiry_prc = max(0, expiry_spot - call_strike)
            call_pnl = call_entry_price - call_expiry_prc

            put_pnl = 0
            if put_strike:
                put_expiry_prc = max(0, put_strike - expiry_spot)
                put_pnl = put_expiry_prc - put_entry_price

            total_pnl = stock_pnl + call_pnl + put_pnl
            total_pnl_pct = (total_pnl / stock_entry_spot) * 100

            results.append({
                "Symbol": sym,
                "Cycle Start": cycle_start.strftime("%Y-%m-%d"),
                "Expiry Date": expiry.strftime("%Y-%m-%d"),
                "Entry Spot": cycle_entry_spot,
                "Expiry Spot": expiry_spot,
                "Call Strike": call_strike,
                "Call Premium": call_entry_price,
                "Put Strike": put_strike if put_strike else "N/A",
                "Put Premium": put_entry_price if put_strike else 0,
                "Net Premium": call_entry_price - (put_entry_price if put_strike else 0),
                "Stock PnL": round(stock_pnl, 2),
                "Options PnL": round(call_pnl + put_pnl, 2),
                "Final PnL": round(total_pnl, 2),
                "Final Return %": round(total_pnl_pct, 2)
            })

        df = pd.DataFrame(results)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='All_FO_Backtest')

        output.seek(0)

        filename = f"CoveredCall_All_FO_{start_date}_to_{end_date}.xlsx"
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        import traceback
        import logging
        logging.error(f"Bulk F&O Export Error: {traceback.format_exc()}")
        # Returning JSON error instead of streaming on fail
        return {"status": "error", "message": str(e)}
