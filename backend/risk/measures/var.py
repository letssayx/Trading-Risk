import numpy as np
from scipy.stats import norm

def calculate_parametric_var(portfolio_value: float, vol: float, confidence: float = 0.99, horizon: int = 1) -> float:
    """
    Calculates Value at Risk (VaR) using Parametric method.
    vol: Daily volatility (decimal).
    """
    z_score = norm.ppf(confidence)
    var = portfolio_value * vol * z_score * np.sqrt(horizon)
    return round(var, 2)

def aggregate_greeks(trades: list) -> dict:
    """
    Sums Delta, Gamma, Vega across trades.
    trades: list of dicts with 'greeks' key.
    """
    net = {"delta": 0.0, "gamma": 0.0, "vega": 0.0}
    for t in trades:
        greeks = t.get('greeks', {})
        qty = t.get('quantity', 0)
        net['delta'] += greeks.get('delta', 0) * qty
        net['gamma'] += greeks.get('gamma', 0) * qty
        net['vega'] += greeks.get('vega', 0) * qty
    return net
