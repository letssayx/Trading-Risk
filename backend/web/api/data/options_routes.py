from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime, timedelta
from backend.infrastructure.db import get_db
from backend.ingest.nse_models import BhavcopyFO, BhavcopyEQ, HistoricalIndexData
import math

router = APIRouter()

# --- Simplified Black-Scholes implementation for on-the-fly calculations ---
def norm_cdf(x):
    """Cumulative distribution function for standard normal distribution"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x):
    """Probability density function for standard normal distribution"""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def bs_d1(S, K, T, r, sigma):
    return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

def bs_d2(d1, T, sigma):
    return d1 - sigma * math.sqrt(T)

def calculate_greeks(S, K, T, r, sigma, is_call):
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0, "iv": sigma}

    try:
        d1 = bs_d1(S, K, T, r, sigma)
        d2 = bs_d2(d1, T, sigma)

        # PDF and CDF
        pdf_d1 = norm_pdf(d1)

        # Greeks
        delta = norm_cdf(d1) if is_call else norm_cdf(d1) - 1.0
        gamma = pdf_d1 / (S * sigma * math.sqrt(T))
        vega = (S * pdf_d1 * math.sqrt(T)) / 100.0

        # Theta (per day)
        term1 = -(S * pdf_d1 * sigma) / (2 * math.sqrt(T))
        if is_call:
            theta = (term1 - r * K * math.exp(-r * T) * norm_cdf(d2)) / 365.0
            rho = (K * T * math.exp(-r * T) * norm_cdf(d2)) / 100.0
        else:
            theta = (term1 + r * K * math.exp(-r * T) * norm_cdf(-d2)) / 365.0
            rho = (-K * T * math.exp(-r * T) * norm_cdf(-d2)) / 100.0

        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho),
            "iv": float(sigma)
        }
    except Exception:
        return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0, "iv": float(sigma)}

def calculate_iv(target_price, S, K, T, r, is_call):
    """ Newton-Raphson approximation for Implied Volatility """
    if T <= 0 or target_price <= 0: return 0.0

    intrinsic = max(0.0, S - K) if is_call else max(0.0, K - S)
    if target_price < intrinsic:
        return 0.001

    sigma = 0.3
    for i in range(100):
        try:
            d1 = bs_d1(S, K, T, r, sigma)
            d2 = bs_d2(d1, T, sigma)

            if is_call:
                price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
            else:
                price = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)

            diff = price - target_price
            if abs(diff) < 1e-4:
                return float(sigma)

            vega = S * norm_pdf(d1) * math.sqrt(T)
            if vega < 1e-8:
                return 0.001

            sigma = sigma - diff / vega
            if sigma <= 0.001:
                return 0.001
            elif sigma > 5.0:
                return 5.0

        except Exception:
            return 0.001

    return float(sigma)


@router.get("/api/data/derivatives/option_chain")
async def get_option_chain(symbol: str, expiry: Optional[str] = None, date: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fetches the option chain for a given symbol and expiry.
    If expiry is not provided, uses the nearest active expiry.
    Calculates Greeks on the fly.
    """
    try:
        symbol = symbol.upper()

        # 1. Determine Target Date
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            latest_fo_date = target_date
        else:
            latest_fo_date_row = db.query(BhavcopyFO.trade_date)\
                                   .filter(BhavcopyFO.instrument_type.in_(['OPTSTK', 'OPTIDX', 'STO', 'IDO', 'OPTIRC']))\
                                   .order_by(desc(BhavcopyFO.trade_date))\
                                   .first()
            if not latest_fo_date_row:
                return {"data": [], "expiries": [], "spot_price": 0.0}
            latest_fo_date = latest_fo_date_row[0]

        # 2. Find Spot Price (EQ or Index)
        spot_price = 0.0

        # Try EQ first
        closest_eq_date_row = db.query(BhavcopyEQ.trade_date)\
                                .filter(BhavcopyEQ.trade_date <= latest_fo_date)\
                                .order_by(desc(BhavcopyEQ.trade_date))\
                                .first()
        if closest_eq_date_row:
            eq_rec = db.query(BhavcopyEQ.close_price)\
                       .filter(BhavcopyEQ.trade_date == closest_eq_date_row[0], BhavcopyEQ.symbol == symbol, BhavcopyEQ.series == 'EQ')\
                       .first()
            if eq_rec:
                spot_price = float(eq_rec[0])

        # If no EQ, try Index
        if spot_price == 0.0:
            idx_name = symbol
            if symbol == 'NIFTY': idx_name = 'NIFTY 50'
            elif symbol == 'BANKNIFTY': idx_name = 'NIFTY BANK'
            elif symbol == 'FINNIFTY': idx_name = 'NIFTY FIN SERVICE'
            elif symbol == 'MIDCPNIFTY': idx_name = 'NIFTY MID SELECT'

            idx_rec = db.query(HistoricalIndexData.close_price)\
                        .filter(HistoricalIndexData.trade_date <= latest_fo_date, HistoricalIndexData.index_name == idx_name)\
                        .order_by(desc(HistoricalIndexData.trade_date))\
                        .first()
            if idx_rec:
                spot_price = float(idx_rec[0])

        # If still 0, try Near Month Futures as spot proxy
        if spot_price == 0.0:
             fut_rec = db.query(BhavcopyFO.close_price)\
                         .filter(BhavcopyFO.trade_date == latest_fo_date, BhavcopyFO.ticker_symb == symbol, BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK']))\
                         .order_by(BhavcopyFO.expiry_date)\
                         .first()
             if fut_rec:
                 spot_price = float(fut_rec[0])

        # 3. Get all valid expiries for this symbol on this date
        expiries_query = db.query(BhavcopyFO.expiry_date)\
                           .filter(BhavcopyFO.trade_date == latest_fo_date, BhavcopyFO.ticker_symb == symbol, BhavcopyFO.instrument_type.in_(['OPTSTK', 'OPTIDX', 'STO', 'IDO', 'OPTIRC']))\
                           .distinct()\
                           .order_by(BhavcopyFO.expiry_date)\
                           .all()

        valid_expiries = [e[0].strftime('%Y-%m-%d') for e in expiries_query]

        if not valid_expiries:
            return {"data": [], "expiries": [], "spot_price": spot_price}

        target_expiry = None
        if expiry:
            # Try to find the exact match
            if expiry in valid_expiries:
                target_expiry = expiry
            else:
                # If the exact expiry doesn't exist for this date, find the closest one that is AFTER the requested expiry
                req_dt = datetime.strptime(expiry, '%Y-%m-%d').date()
                for ve in valid_expiries:
                    ve_dt = datetime.strptime(ve, '%Y-%m-%d').date()
                    if ve_dt >= req_dt:
                        target_expiry = ve
                        break

        # Fallback to the first available expiry
        if not target_expiry:
             target_expiry = valid_expiries[0]

        target_expiry_date = datetime.strptime(target_expiry, '%Y-%m-%d').date()

        # 4. Fetch the Option Chain Data
        opt_records = db.query(
            BhavcopyFO.strike_price,
            BhavcopyFO.option_type,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest,
            BhavcopyFO.change_in_oi,
            BhavcopyFO.total_trading_vol,
            BhavcopyFO.avg_price
        ).filter(
            BhavcopyFO.trade_date == latest_fo_date,
            BhavcopyFO.ticker_symb == symbol,
            BhavcopyFO.expiry_date == target_expiry_date,
            BhavcopyFO.instrument_type.in_(['OPTSTK', 'OPTIDX', 'STO', 'IDO', 'OPTIRC'])
        ).all()

        # 5. Process and Calculate Greeks
        chain = {}
        dte = (target_expiry_date - latest_fo_date).days
        T_years = dte / 365.0
        r = 0.05 # 5% Risk Free Rate assumption

        for r_obj in opt_records:
            strike = float(r_obj.strike_price)
            opt_type = r_obj.option_type.upper() # CE or PE

            if strike not in chain:
                chain[strike] = {
                    "strike": strike,
                    "CE": {"price": 0, "oi": 0, "chg_oi": 0, "vol": 0, "iv": 0, "delta": 0, "gamma": 0, "theta": 0, "vega": 0},
                    "PE": {"price": 0, "oi": 0, "chg_oi": 0, "vol": 0, "iv": 0, "delta": 0, "gamma": 0, "theta": 0, "vega": 0}
                }

            is_call = opt_type == 'CE'
            price = float(r_obj.close_price)

            # If price is 0, use avg_price as fallback
            if price == 0.0 and r_obj.avg_price:
                 price = float(r_obj.avg_price)

            # Calculate Greeks if we have a spot price and time
            greeks = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "iv": 0.0}
            if spot_price > 0 and T_years > 0 and price > 0:
                iv = calculate_iv(price, spot_price, strike, T_years, r, is_call)
                if iv > 0.001 and iv < 5.0: # Cap IV to realistic bounds
                    greeks = calculate_greeks(spot_price, strike, T_years, r, iv, is_call)
                    greeks["iv"] = iv * 100 # Convert to % for UI

            chain[strike][opt_type] = {
                "price": price,
                "oi": int(r_obj.open_interest) if r_obj.open_interest else 0,
                "chg_oi": int(r_obj.change_in_oi) if r_obj.change_in_oi else 0,
                "vol": int(r_obj.total_trading_vol) if r_obj.total_trading_vol else 0,
                "iv": greeks.get("iv", 0.0),
                "delta": greeks.get("delta", 0.0),
                "gamma": greeks.get("gamma", 0.0),
                "theta": greeks.get("theta", 0.0),
                "vega": greeks.get("vega", 0.0)
            }

        # Return sorted by strike
        sorted_chain = [chain[k] for k in sorted(chain.keys())]

        return {
            "data": sorted_chain,
            "expiries": valid_expiries,
            "selected_expiry": target_expiry,
            "spot_price": spot_price,
            "date": latest_fo_date.strftime('%Y-%m-%d')
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
