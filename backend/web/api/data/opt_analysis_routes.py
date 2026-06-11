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
        from backend.ingest.nse_models import HistoricalIndexData, BhavcopyEQ
        import pandas as pd

        symbol = symbol.upper()

        # Format index names
        is_index = False
        formatted_index_name = symbol
        if symbol == 'NIFTY':
            formatted_index_name = 'Nifty 50'
            is_index = True
        elif symbol == 'BANKNIFTY':
            formatted_index_name = 'Nifty Bank'
            is_index = True
        elif symbol == 'FINNIFTY':
            formatted_index_name = 'Nifty Fin Service'
            is_index = True
        elif symbol == 'MIDCPNIFTY':
            formatted_index_name = 'Nifty Midcap 50'
            is_index = True

        # Get trade dates
        if expiry_only:
            dates_query = text("SELECT DISTINCT expiry_date as d FROM bhavcopy_fo WHERE ticker_symb = :symbol AND expiry_date <= CURRENT_DATE ORDER BY expiry_date DESC LIMIT :limit")
        else:
            dates_query = text("SELECT DISTINCT trade_date as d FROM bhavcopy_fo WHERE ticker_symb = :symbol AND trade_date <= CURRENT_DATE ORDER BY trade_date DESC LIMIT :limit")

        dates_res = db.execute(dates_query, {"symbol": symbol, "limit": int(days)}).fetchall()
        valid_dates = sorted([r[0] for r in dates_res])

        if not valid_dates:
            return {"dates": [], "price": [], "ce_oi": [], "pe_oi": [], "total_oi": [], "fut_oi": [], "pcr": []}

        dates_tuple = tuple(str(d) for d in valid_dates)

        # Get Spot Prices
        spot_prices = {}
        if is_index:
            spot_query = text("SELECT trade_date, close_price FROM historical_index_data WHERE index_name = :index_name AND trade_date IN :dates")
            spot_res = db.execute(spot_query, {"index_name": formatted_index_name, "dates": dates_tuple}).fetchall()
            for r in spot_res:
                spot_prices[r[0]] = float(r[1])
        else:
            spot_query = text("SELECT trade_date, close_price FROM bhavcopy_eq WHERE symbol = :symbol AND series = 'EQ' AND trade_date IN :dates")
            spot_res = db.execute(spot_query, {"symbol": symbol, "dates": dates_tuple}).fetchall()
            for r in spot_res:
                spot_prices[r[0]] = float(r[1])

        # Get Futures OI
        fut_query = text("""
            SELECT trade_date, SUM(open_interest)
            FROM bhavcopy_fo
            WHERE ticker_symb = :symbol
            AND instrument_type IN ('FUTIDX', 'FUTSTK')
            AND trade_date IN :dates
            GROUP BY trade_date
        """)
        fut_res = db.execute(fut_query, {"symbol": symbol, "dates": dates_tuple}).fetchall()
        fut_oi_map = {r[0]: int(r[1]) for r in fut_res}

        # Get Options for Delta-adjusted OI
        opt_query = text("""
            SELECT trade_date, option_type, strike_price, expiry_date, SUM(open_interest) as oi
            FROM bhavcopy_fo
            WHERE ticker_symb = :symbol
            AND instrument_type IN ('OPTIDX', 'OPTSTK')
            AND trade_date IN :dates
            GROUP BY trade_date, option_type, strike_price, expiry_date
        """)
        opt_res = db.execute(opt_query, {"symbol": symbol, "dates": dates_tuple}).fetchall()

        df_opt = pd.DataFrame(opt_res, columns=['trade_date', 'option_type', 'strike_price', 'expiry_date', 'oi'])

        # Prepare Delta calc
        ce_delta_oi_map = {d: 0.0 for d in valid_dates}
        pe_delta_oi_map = {d: 0.0 for d in valid_dates}

        if not df_opt.empty:
            df_opt['spot'] = df_opt['trade_date'].map(spot_prices)
            # Fill missing spots with an arbitrary number to avoid math errors if spot is missing
            df_opt['spot'] = df_opt['spot'].fillna(df_opt['strike_price'])

            # Days to Expiry
            df_opt['trade_date'] = pd.to_datetime(df_opt['trade_date'])
            df_opt['expiry_date'] = pd.to_datetime(df_opt['expiry_date'])
            df_opt['dte'] = (df_opt['expiry_date'] - df_opt['trade_date']).dt.days
            df_opt['T'] = df_opt['dte'] / 365.0

            # Assume 10% Risk-Free Rate and 20% flat Volatility for delta calculation if IV is missing
            # In a full impl we might fetch ATM IV, but standard delta approximation uses fixed inputs if needed
            df_opt['r'] = 0.10
            df_opt['sigma'] = 0.20

            # Calculate Delta
            df_opt['is_call'] = df_opt['option_type'] == 'CE'
            df_opt['delta'] = calc_bs_delta_vectorized(
                df_opt['spot'].values,
                df_opt['strike_price'].values,
                df_opt['T'].values,
                df_opt['r'].values,
                df_opt['sigma'].values,
                df_opt['is_call'].values
            )

            df_opt['delta_oi'] = df_opt['oi'] * df_opt['delta'].abs()

            for trade_date, group in df_opt.groupby('trade_date'):
                d = trade_date.date()
                ce_delta_oi_map[d] = group[group['is_call']]['delta_oi'].sum()
                pe_delta_oi_map[d] = group[~group['is_call']]['delta_oi'].sum()

        result_dates = []
        result_prices = []
        result_ce_oi = []
        result_pe_oi = []
        result_total_oi = []
        result_fut_oi = []
        result_pcr = []

        for d in valid_dates:
            result_dates.append(d.strftime('%Y-%m-%d'))
            result_prices.append(spot_prices.get(d, 0.0))

            ce = ce_delta_oi_map.get(d, 0)
            pe = pe_delta_oi_map.get(d, 0)
            result_ce_oi.append(int(ce))
            result_pe_oi.append(int(pe))

            f_oi = fut_oi_map.get(d, 0)
            result_fut_oi.append(f_oi)

            tot_oi = int(ce + pe + f_oi)
            result_total_oi.append(tot_oi)

            pcr = (pe / ce) if ce > 0 else 0.0
            result_pcr.append(float(round(pcr, 4)))

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
