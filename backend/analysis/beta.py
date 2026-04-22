import numpy as np
import pandas as pd

def calculate_beta(
    asset_returns: pd.Series,
    market_returns: pd.Series,
    window: int = 252
) -> float:
    """
    Calculates rolling Beta: Cov(Asset, Market) / Var(Market).
    Default window is 252 days (1 year).
    """
    # Align data
    df = pd.DataFrame({"asset": asset_returns, "market": market_returns}).dropna()

    if len(df) < window:
        # Use available data if less than window, but warn?
        # For robustness, just calculate on what we have
        pass

    cov_matrix = np.cov(df["asset"], df["market"])
    covariance = cov_matrix[0, 1]
    market_variance = cov_matrix[1, 1]

    if market_variance == 0:
        return 0.0

    beta = covariance / market_variance
    return beta

def calculate_rolling_beta(
    asset_returns: pd.Series,
    market_returns: pd.Series,
    window: int = 252
) -> pd.Series:
    """
    Returns time series of rolling beta.
    """
    # Align
    df = pd.DataFrame({"asset": asset_returns, "market": market_returns}).dropna()

    rolling_cov = df["asset"].rolling(window=window).cov(df["market"])
    rolling_var = df["market"].rolling(window=window).var()

    return rolling_cov / rolling_var
