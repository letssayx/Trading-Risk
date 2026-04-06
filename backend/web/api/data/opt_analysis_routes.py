from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.infrastructure.db import get_db
import pandas as pd
import numpy as np
from datetime import datetime, date

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
        symbol = symbol.upper()

        # We need historical futures prices, Option OI, and we calculate delta weighted Option OI using BS.

        # 1. Fetch distinct trade dates up to `days` limit
        # If expiry_only is true, filter dates to only those that are an expiry date for this symbol
        if expiry_only:
            dates_query = text("""
                WITH expiries AS (
                    SELECT DISTINCT expiry_date
                    FROM bhavcopy_fo
                    WHERE ticker_symb = :symbol
                ),
                valid_dates AS (
                    SELECT DISTINCT trade_date
                    FROM bhavcopy_fo
                    WHERE ticker_symb = :symbol
                      AND trade_date IN (SELECT expiry_date FROM expiries)
                )
                SELECT trade_date
                FROM valid_dates
                ORDER BY trade_date DESC
                LIMIT :days
            """)
        else:
            dates_query = text("""
                SELECT DISTINCT trade_date
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                ORDER BY trade_date DESC
                LIMIT :days
            """)

        dates_result = db.execute(dates_query, {"symbol": symbol, "days": days}).fetchall()
        if not dates_result:
            return {"dates": [], "price": [], "ce_oi": [], "pe_oi": [], "total_oi": [], "pcr": []}

        dates = sorted([r[0] for r in dates_result])
        min_date = dates[0]
        max_date = dates[-1]

        # 2. Fetch Near Month Futures Price and Total Futures OI
        fut_query = text("""
            WITH fut_price AS (
                SELECT
                    trade_date,
                    close_price as fut_close,
                    ROW_NUMBER() OVER (PARTITION BY trade_date ORDER BY expiry_date ASC) as rn
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND instrument_type IN ('FUTIDX', 'FUTSTK', 'STF', 'IDF')
                  AND expiry_date >= trade_date
                  AND trade_date BETWEEN :min_date AND :max_date
            ),
            fut_oi AS (
                SELECT
                    trade_date,
                    SUM(open_interest) as total_fut_oi
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND instrument_type IN ('FUTIDX', 'FUTSTK', 'STF', 'IDF')
                  AND trade_date BETWEEN :min_date AND :max_date
                GROUP BY trade_date
            )
            SELECT f.trade_date, f.fut_close, foi.total_fut_oi
            FROM fut_price f
            LEFT JOIN fut_oi foi ON f.trade_date = foi.trade_date
            WHERE f.rn = 1
        """)
        fut_df = pd.read_sql(fut_query, db.connection(), params={"symbol": symbol, "min_date": min_date, "max_date": max_date})
        if fut_df.empty:
            return {"dates": [], "price": [], "ce_oi": [], "pe_oi": [], "total_oi": [], "pcr": []}

        fut_df.set_index('trade_date', inplace=True)

        # 3. Fetch Options Data
        opt_query = text("""
            SELECT
                trade_date,
                expiry_date,
                strike_price,
                option_type,
                open_interest
            FROM bhavcopy_fo
            WHERE ticker_symb = :symbol
              AND instrument_type IN ('OPTIDX', 'OPTSTK', 'STO', 'IDO')
              AND trade_date BETWEEN :min_date AND :max_date
              AND open_interest > 0
        """)
        opt_df = pd.read_sql(opt_query, db.connection(), params={"symbol": symbol, "min_date": min_date, "max_date": max_date})

        # 4. Fetch Volatility (Daily)
        vol_query = text("""
            SELECT trade_date, applicable_annualised_vol
            FROM fo_volatility
            WHERE symbol = :symbol AND trade_date BETWEEN :min_date AND :max_date
        """)
        vol_df = pd.read_sql(vol_query, db.connection(), params={"symbol": symbol, "min_date": min_date, "max_date": max_date})
        vol_df.set_index('trade_date', inplace=True)

        # Create output arrays
        result_dates = []
        result_prices = []
        result_ce_oi = []
        result_pe_oi = []
        result_total_oi = []
        result_pcr = []

        # If options data exists, vector calculate BS Delta
        if not opt_df.empty:
            # Map futures close price and volatility to options dataframe
            opt_df['fut_close'] = opt_df['trade_date'].map(fut_df['fut_close']).fillna(0)

            # Map volatility - Default to 20% if missing
            if not vol_df.empty:
                opt_df['sigma'] = opt_df['trade_date'].map(vol_df['applicable_annualised_vol'])
            else:
                opt_df['sigma'] = 0.20
            opt_df['sigma'] = opt_df['sigma'].fillna(0.20)

            # Calculate Time to Expiry (T) in years
            # Convert dates to pandas datetime for subtraction
            trade_dt = pd.to_datetime(opt_df['trade_date'])
            expiry_dt = pd.to_datetime(opt_df['expiry_date'])
            opt_df['T'] = (expiry_dt - trade_dt).dt.days / 365.0

            # Calculate Delta
            is_call = opt_df['option_type'] == 'CE'

            # Vectorized call
            try:
                opt_df['delta'] = calc_bs_delta_vectorized(
                    opt_df['fut_close'].values,
                    opt_df['strike_price'].values,
                    opt_df['T'].values,
                    0.0, # risk-free rate
                    opt_df['sigma'].values,
                    is_call.values
                )
                opt_df['delta_weighted_oi'] = opt_df['open_interest'] * np.abs(opt_df['delta'])
            except Exception as e:
                # Fallback to naive delta if math error
                print(f"Error calculating delta: {e}")
                opt_df['delta'] = np.where(is_call, 0.5, -0.5)
                opt_df['delta_weighted_oi'] = opt_df['open_interest'] * 0.5

            # Aggregate per day
            agg_df = opt_df.groupby('trade_date').apply(lambda x: pd.Series({
                'ce_oi': x.loc[x['option_type'] == 'CE', 'open_interest'].sum(),
                'pe_oi': x.loc[x['option_type'] == 'PE', 'open_interest'].sum(),
                'delta_weighted_opt_oi': x['delta_weighted_oi'].sum()
            })).reset_index()
            agg_df.set_index('trade_date', inplace=True)

        else:
            agg_df = pd.DataFrame(columns=['ce_oi', 'pe_oi', 'delta_weighted_opt_oi'])

        # Build final response
        for d in dates:
            if d not in fut_df.index:
                continue

            price = float(fut_df.loc[d, 'fut_close'])
            total_fut_oi = float(fut_df.loc[d, 'total_fut_oi']) if pd.notna(fut_df.loc[d, 'total_fut_oi']) else 0

            ce_oi = 0
            pe_oi = 0
            delta_opt_oi = 0

            if d in agg_df.index:
                ce_oi = int(agg_df.loc[d, 'ce_oi'])
                pe_oi = int(agg_df.loc[d, 'pe_oi'])
                delta_opt_oi = float(agg_df.loc[d, 'delta_weighted_opt_oi'])

            total_oi = int(total_fut_oi + delta_opt_oi)
            pcr = float(pe_oi / ce_oi) if ce_oi > 0 else 0.0

            result_dates.append(d.strftime('%Y-%m-%d'))
            result_prices.append(price)
            result_ce_oi.append(ce_oi)
            result_pe_oi.append(pe_oi)
            result_total_oi.append(total_oi)
            result_pcr.append(round(pcr, 4))

        return {
            "dates": result_dates,
            "price": result_prices,
            "ce_oi": result_ce_oi,
            "pe_oi": result_pe_oi,
            "total_oi": result_total_oi,
            "pcr": result_pcr
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
