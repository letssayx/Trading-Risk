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
        # Fetch historical prices to calculate realized volatility
        query = text("""
            SELECT trade_date, close_price
            FROM bhavcopy_eq
            WHERE ticker_symb = :symbol
            ORDER BY trade_date ASC
        """)
        # If NIFTY/BANKNIFTY, we might need historical_index_data. Handle fallback.
        if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
            query = text("""
                SELECT trade_date, close_price
                FROM historical_index_data
                WHERE index_name = :symbol
                ORDER BY trade_date ASC
            """)

        result = db.execute(query, {"symbol": symbol}).fetchall()

        if not result or len(result) < 500:
            raise HTTPException(status_code=400, detail="Insufficient price history for Volatility Cone")

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
                cone_data["current_rv"].append(round(rolling_rv[-1], 2))
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
        if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
            query = text("""
                SELECT trade_date, close_price
                FROM historical_index_data
                WHERE index_name = :symbol
                ORDER BY trade_date DESC
                LIMIT :lookback
            """)

        result = db.execute(query, {"symbol": symbol, "lookback": lookback_days}).fetchall()
        result.reverse() # Sort ascending

        if not result:
            return {"dates": [], "prices": [], "expiries": [], "rv": [], "boxes": []}

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
