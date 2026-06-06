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
                OiAnalysisMetrics.trade_date.in_(valid_dates)
            ).order_by(desc(OiAnalysisMetrics.trade_date)).limit(days).all()
        else:
            query = db.query(OiAnalysisMetrics).filter(
                OiAnalysisMetrics.symbol == symbol
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
