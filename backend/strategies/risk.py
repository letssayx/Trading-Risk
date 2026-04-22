from typing import Dict, Any

def get_risk_dashboard_data(
    portfolio_beta: float,
    market_return: float, # Percentage e.g. 0.015
    var_95: float, # Dollar value
    var_se: float, # Dollar value
    svar_95: float = 0.0
) -> Dict[str, Any]:
    """
    Calculates unified Risk Dashboard metrics.

    Args:
        portfolio_beta: Weighted beta of the portfolio.
        market_return: Today's Nifty/Benchmark return.
        var_95: Daily VaR (95%).
        var_se: Standard Error of VaR.

    Returns:
        Dict with:
        - Nifty Drag (PnL attributable to Beta)
        - VaR Confidence Band (Upper, Lower)
        - Precision Warning
    """

    # Nifty Drag: If Market +1% and Beta 1.5 -> Expected Return 1.5%
    # This is the "Beta Contribution" or "Systematic PnL"
    # Wait, Drag implies negative? Or just beta contribution?
    # Prompt: "Show how much of today's PnL came from the Market Move (Beta)"

    # Assuming PnL = Beta * Market_Ret * NAV?
    # Or just return percentage?
    # Let's return percentage contribution.

    beta_pnl_pct = portfolio_beta * market_return

    # Confidence Band
    var_upper = var_95 + var_se
    var_lower = max(0, var_95 - var_se)

    precision_status = "STABLE"
    if var_95 > 0 and (var_se / var_95) > 0.10:
        precision_status = "LOW_PRECISION"

    return {
        "nifty_drag_pct": beta_pnl_pct,
        "nifty_drag_label": f"{beta_pnl_pct*100:+.2f}% due to Market Beta",
        "var_confidence_band": {
            "value": var_95,
            "upper": var_upper,
            "lower": var_lower,
            "se_percent": (var_se / var_95 * 100) if var_95 > 0 else 0
        },
        "precision_status": precision_status,
        "stressed_divergence": (svar_95 / var_95) if var_95 > 0 else 0
    }
