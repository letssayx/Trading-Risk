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
        from backend.ingest.nse_models import OiAnalysisMetrics, BhavcopyFO
        symbol = symbol.upper()

        if expiry_only:
            # Join with BhavcopyFO to find expiry dates
            # A trade date is an expiry date if there is any instrument expiring on that day for this symbol
            records = db.query(
                OiAnalysisMetrics.trade_date,
                OiAnalysisMetrics.price,
                OiAnalysisMetrics.call_oi,
                OiAnalysisMetrics.put_oi,
                OiAnalysisMetrics.total_oi,
                OiAnalysisMetrics.pcr
            ).join(
                BhavcopyFO,
                (OiAnalysisMetrics.trade_date == BhavcopyFO.expiry_date) &
                (OiAnalysisMetrics.symbol == BhavcopyFO.ticker_symb)
            ).filter(
                OiAnalysisMetrics.symbol == symbol
            ).distinct().order_by(OiAnalysisMetrics.trade_date.desc()).limit(days).all()
        else:
            records = db.query(
                OiAnalysisMetrics.trade_date,
                OiAnalysisMetrics.price,
                OiAnalysisMetrics.call_oi,
                OiAnalysisMetrics.put_oi,
                OiAnalysisMetrics.total_oi,
                OiAnalysisMetrics.pcr
            ).filter(
                OiAnalysisMetrics.symbol == symbol
            ).order_by(OiAnalysisMetrics.trade_date.desc()).limit(days).all()

        if not records:
            return {"dates": [], "price": [], "ce_oi": [], "pe_oi": [], "total_oi": [], "pcr": []}

        # Need ascending order for charting
        records = list(reversed(records))

        result_dates = []
        result_prices = []
        result_ce_oi = []
        result_pe_oi = []
        result_total_oi = []
        result_pcr = []

        for r in records:
            result_dates.append(str(r.trade_date))
            result_prices.append(r.price or 0.0)
            result_ce_oi.append(r.call_oi or 0)
            result_pe_oi.append(r.put_oi or 0)
            result_total_oi.append(r.total_oi or 0)
            result_pcr.append(r.pcr or 0.0)

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
