from typing import Dict

def interpret_iv_skew(
    iv_call: float,
    iv_put: float,
    atm_iv: float
) -> Dict[str, str]:
    """
    Interprets Volatility Skew (Put/Call IV difference) to suggest strategies.

    Args:
        iv_call: Implied Volatility of OTM Call (e.g. 105%).
        iv_put: Implied Volatility of OTM Put (e.g. 95%).
        atm_iv: At-The-Money Implied Volatility.

    Returns:
        Dict with 'skew_type' (Call Skew/Put Skew) and 'suggested_action'.
    """
    skew_diff = iv_put - iv_call

    # Put Skew (Standard): Puts are more expensive (Crash protection demand)
    # Call Skew (Bullish): Calls are more expensive (Upside speculation)

    skew_type = "NEUTRAL"
    action = "Long/Short Straddle"

    if skew_diff > 2.0: # Significant Put Skew
        skew_type = "PUT_SKEW"
        action = "Put Writing (Sell expensive Puts) / Bull Put Spread"
    elif skew_diff < -2.0: # Significant Call Skew
        skew_type = "CALL_SKEW"
        action = "Call Writing (Sell expensive Calls) / Bear Call Spread"

    # IV Rank Logic (implied, using ATM IV level relative to history)
    # Assuming atm_iv is absolute level here.
    # If IV is high (>30?), prefer Selling. If Low (<12?), prefer Buying.

    bias = "NEUTRAL"
    if atm_iv > 30:
        bias = "SELL_PREMIUM"
    elif atm_iv < 15:
        bias = "BUY_PREMIUM"

    return {
        "skew_type": skew_type,
        "suggested_action": f"{bias} | {action}",
        "skew_diff": round(skew_diff, 2)
    }

def calculate_theta_vega_ratio(
    theta: float,
    vega: float
) -> float:
    """
    Calculates Theta/Vega Ratio for Volatility Arbitrage efficiency.
    Theta (Time Decay) / Vega (Vol Sensitivity).
    High Ratio (>2?) suggests good efficiency (High decay for low vol risk).
    """
    if abs(vega) < 1e-9:
        return 0.0 # Avoid div by zero

    # Theta is usually negative for long options, positive for short.
    # We care about the absolute efficiency for income strategies (short theta is negative pnl? No, short option has positive theta pnl).
    # Usually we look at Portfolio Theta (positive for sellers) vs Portfolio Vega (risk).

    return abs(theta / vega)
