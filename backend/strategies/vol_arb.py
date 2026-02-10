from typing import Dict, Any, List
import numpy as np

def calculate_vol_spread(
    iv_near: float, # Near-month implied volatility
    iv_far: float, # Far-month implied volatility
) -> Dict[str, Any]:
    """
    Calculates Calendar Spread (Term Structure) logic.
    "Calendar King": If Near IV >> Far IV (Backwardation), Buy Calendar (Long Far, Short Near).
    If Near IV << Far IV (Contango), Sell Calendar (Short Far, Long Near) or just Debit spread.
    Wait, usually we buy calendars when Near IV is low (cheap to buy front) and expected to rise?
    Or sell front (high IV) buy back (low IV)? -> Yes, Short High IV, Long Low IV.

    Backwardation (Near > Far): Sell Near Call, Buy Far Call. (Short Calendar).
    Contango (Near < Far): Buy Near Call, Sell Far Call? No, usually Long Calendar = Long Far, Short Near.
    The edge is in the IV differential collapsing or expanding.

    If Ratio > 1.2 (Backwardation): Great for Income Calendars (Short Front).
    """
    spread = iv_near - iv_far
    ratio = iv_near / iv_far if iv_far > 0 else 0

    signal = "NEUTRAL"
    if ratio > 1.15:
        signal = "SHORT_CALENDAR_OPP" # Sell front premium
    elif ratio < 0.85:
        signal = "LONG_CALENDAR_OPP" # Buy front premium? Or just cheap term structure.

    return {
        "spread": spread,
        "ratio": ratio,
        "signal": signal,
        "strategy": "Calendar Spread"
    }

def calculate_theta_efficiency(
    theta: float,
    vega: float
) -> float:
    """
    Theta/Vega Ratio. High ratio (>2) implies efficient time decay capture relative to volatility risk.
    """
    if abs(vega) < 1e-9:
        return 0.0
    return abs(theta / vega)
