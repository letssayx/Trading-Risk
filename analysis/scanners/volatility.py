from typing import Dict, Any
import pandas as pd

def calculate_iv_metrics(current_iv: float, historical_iv_series: pd.Series) -> Dict[str, Any]:
    """
    Computes IV Rank and IV Percentile to determine if vol is 'cheap' or 'expensive'.
    """
    if historical_iv_series.empty:
        return {"rank": 0, "percentile": 0, "regime": "Unknown"}

    iv_min = historical_iv_series.min()
    iv_max = historical_iv_series.max()

    # IV Rank: Where today's IV sits in the absolute high-low range
    if iv_max == iv_min:
        iv_rank = 0.0
    else:
        iv_rank = ((current_iv - iv_min) / (iv_max - iv_min)) * 100

    # IV Percentile: % of days in the past year where IV was lower than today
    iv_percentile = (historical_iv_series < current_iv).mean() * 100

    regime = "Neutral"
    if iv_rank > 80:
        regime = "High/Sell"
    elif iv_rank < 20:
        regime = "Low/Buy"

    return {
        "rank": round(iv_rank, 1),
        "percentile": round(iv_percentile, 1),
        "regime": regime
    }
