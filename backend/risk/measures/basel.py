import numpy as np
import pandas as pd
from typing import Tuple
from scipy.stats import norm

def calculate_historical_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    lookback: int = 500
) -> float:
    """
    Calculates Historical VaR using the specified lookback window (default 500 days).
    """
    if len(returns) < lookback:
        # Use available
        window = returns
    else:
        window = returns.iloc[-lookback:]

    var_percentile = (1 - confidence_level) * 100
    var = np.percentile(window, var_percentile)
    return abs(var) # Return positive VaR

def calculate_parametric_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    lookback: int = 500
) -> Tuple[float, float]:
    """
    Calculates Parametric VaR (Normal Distribution) using lookback window.
    Returns (VaR, Sigma).
    """
    if len(returns) < lookback:
        window = returns
    else:
        window = returns.iloc[-lookback:]

    mu = window.mean()
    sigma = window.std()

    z = norm.ppf(confidence_level)
    # VaR = -(mu - z * sigma)
    # Usually assume mu ~ 0 for short horizons
    var = abs(mu - z * sigma)

    return var, sigma

def calculate_var_se(
    sigma: float,
    n: int = 500,
    confidence_level: float = 0.95
) -> float:
    """
    Calculates Standard Error of VaR.
    SE_VaR = sigma * sqrt( (1 + z^2/2) / n )
    """
    z = norm.ppf(confidence_level)
    term = (1 + (z**2) / 2.0)
    se = sigma * np.sqrt(term / n)
    return se

def calibrate_stress_period(
    returns: pd.Series,
    window_size: int = 251
) -> Tuple[pd.Series, str]:
    """
    Scans history to find the 251-day period with highest volatility.
    Returns the stress window and start date.
    """
    if len(returns) < window_size:
        return returns, "Insufficient History"

    rolling_vol = returns.rolling(window=window_size).std()
    max_vol_idx = rolling_vol.idxmax()

    if pd.isna(max_vol_idx):
        return returns.iloc[-window_size:], "No Valid Volatility"

    # Extract window ending at max_vol_idx
    end_loc = returns.index.get_loc(max_vol_idx)
    start_loc = max(0, end_loc - window_size + 1)

    stress_window = returns.iloc[start_loc : end_loc + 1]
    return stress_window, str(max_vol_idx.date())

def calculate_stressed_var(
    stress_returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculates 95% VaR on the stressed window.
    """
    return calculate_historical_var(stress_returns, confidence_level, lookback=len(stress_returns))

def calculate_stressed_es(
    stress_returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculates Expected Shortfall (CVaR) on the stressed window.
    Average of losses exceeding VaR.
    """
    var = calculate_stressed_var(stress_returns, confidence_level)
    losses = stress_returns[stress_returns <= -var]
    if len(losses) == 0:
        return var # Fallback
    return abs(losses.mean())
