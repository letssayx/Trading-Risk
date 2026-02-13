from typing import Dict, List, Optional
import numpy as np
from scipy.stats import norm
from backend.domain.portfolio.models import Trade, TradeSide, TradeStatus

def calculate_total_greeks(trades: List[Trade]) -> Dict[str, float]:
    """
    Aggregates Greek exposures (Delta, Gamma, Vega, Theta, Rho) from a list of trades.

    Iterates through all open trades and sums up their individual greek exposures
    based on the trade direction (Long/Short).

    Args:
        trades (List[Trade]): A list of Trade objects. Each trade is expected
            to have a 'greeks' dictionary in its `meta_data` attribute.

    Returns:
        Dict[str, float]: A dictionary containing the aggregated values for:
            - delta: Sensitivity to underlying price change.
            - gamma: Sensitivity of Delta to underlying price change.
            - vega: Sensitivity to volatility change.
            - theta: Sensitivity to time decay.
            - rho: Sensitivity to interest rate change.
    """
    aggregated: Dict[str, float] = {
        "delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0
    }

    for trade in trades:
        # Check if trade is effectively open
        if trade.status == TradeStatus.OPEN:
            _accumulate_trade_greeks(trade, aggregated)

    return aggregated


def _accumulate_trade_greeks(trade: Trade, acc: Dict[str, float]) -> None:
    """
    Accumulates the greeks for a single trade into the accumulator dictionary.

    Args:
        trade (Trade): The trade object containing greek data.
        acc (Dict[str, float]): The accumulator dictionary to update in-place.
    """
    greeks: Dict[str, float] = trade.meta_data.get("greeks", {}) or {}
    qty: float = float(trade.qty)

    # Direction: 1 for Buy (Long), -1 for Sell (Short)
    direction: int = 1 if trade.side == TradeSide.BUY else -1

    # Apply direction to Greeks
    for key in acc.keys():
        val = greeks.get(key, 0.0)
        acc[key] += val * qty * direction


def calculate_option_greeks(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> Dict[str, float]:
    """
    Calculates Black-Scholes Greeks for a European option.

    Args:
        S (float): Current price of the underlying asset.
        K (float): Strike price of the option.
        T (float): Time to expiration in years.
        r (float): Risk-free interest rate (annualized).
        sigma (float): Volatility of the underlying asset (annualized).
        option_type (str): Type of option, either "call" or "put". Defaults to "call".

    Returns:
        Dict[str, float]: Dictionary containing calculated greeks:
            delta, gamma, vega, theta, rho.
    """
    if T <= 0 or sigma <= 0:
        return {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    is_call = option_type.lower() == "call"

    # Cumulative Normal Distribution
    cdf_d1 = norm.cdf(d1)
    cdf_neg_d1 = norm.cdf(-d1)
    cdf_d2 = norm.cdf(d2)
    cdf_neg_d2 = norm.cdf(-d2)

    # Probability Density Function
    pdf_d1 = norm.pdf(d1)

    # Delta
    delta = cdf_d1 if is_call else (cdf_d1 - 1.0)

    # Gamma (Same for Call and Put)
    gamma = pdf_d1 / (S * sigma * np.sqrt(T))

    # Vega (Same for Call and Put)
    # Usually reported per 1% vol change -> divide by 100
    vega = (S * pdf_d1 * np.sqrt(T)) / 100.0

    # Theta
    # Usually reported per 1 day decay -> divide by 365
    term1 = -(S * pdf_d1 * sigma) / (2 * np.sqrt(T))
    if is_call:
        theta_annual = term1 - r * K * np.exp(-r * T) * cdf_d2
    else:
        theta_annual = term1 + r * K * np.exp(-r * T) * cdf_neg_d2
    theta = theta_annual / 365.0

    # Rho
    # Usually reported per 1% rate change -> divide by 100
    if is_call:
        rho_annual = K * T * np.exp(-r * T) * cdf_d2
    else:
        rho_annual = -K * T * np.exp(-r * T) * cdf_neg_d2
    rho = rho_annual / 100.0

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega),
        "theta": float(theta),
        "rho": float(rho)
    }
