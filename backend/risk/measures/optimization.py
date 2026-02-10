import numpy as np
import pandas as pd
from typing import Union
from scipy.stats import norm

def calculate_marginal_var(
    weights: Union[np.ndarray, pd.Series],
    cov_matrix: Union[np.ndarray, pd.DataFrame],
    alpha: float = 0.05
) -> pd.Series:
    """
    Calculates Marginal VaR (MVaR) using Euler decomposition for a Normal distribution.
    MVaR_i = (Cov * w)_i / sqrt(w' * Cov * w) * Z_alpha

    Args:
        weights: Portfolio weights (n,)
        cov_matrix: Covariance matrix of asset returns (n, n)
        alpha: Significance level (e.g., 0.05 for 95% confidence)

    Returns:
        pd.Series: Marginal VaR for each asset.
    """
    # Convert to numpy arrays if pandas objects
    w = weights.values if isinstance(weights, pd.Series) else weights
    cov = cov_matrix.values if isinstance(cov_matrix, pd.DataFrame) else cov_matrix

    # Portfolio Variance
    port_var = np.dot(w.T, np.dot(cov, w))
    port_std = np.sqrt(port_var)

    # Z-score for alpha
    z_score = norm.ppf(1 - alpha)

    # Marginal Contribution to Risk (MCR) / Marginal VaR
    # MVaR = z * (Cov * w) / sigma_p
    cov_w = np.dot(cov, w)

    # Handle division by zero if volatility is effectively zero
    if port_std < 1e-9:
        return pd.Series(np.zeros_like(w))

    mvar = z_score * cov_w / port_std

    return pd.Series(mvar)

def calculate_component_var(
    weights: Union[np.ndarray, pd.Series],
    cov_matrix: Union[np.ndarray, pd.DataFrame],
    alpha: float = 0.05
) -> pd.Series:
    """
    Calculates Component VaR (CVaR) using Euler decomposition.
    CVaR_i = w_i * MVaR_i
    Sum(CVaR_i) = Total VaR

    Args:
        weights: Portfolio weights
        cov_matrix: Covariance matrix
        alpha: Significance level

    Returns:
        pd.Series: Component VaR for each asset.
    """
    mvar = calculate_marginal_var(weights, cov_matrix, alpha)

    w = weights if isinstance(weights, pd.Series) else pd.Series(weights)
    # Ensure indices align if using pandas
    if isinstance(mvar, pd.Series) and isinstance(w, pd.Series):
        mvar.index = w.index

    cvar = w * mvar
    return cvar

def calculate_risk_contributions(
    weights: Union[np.ndarray, pd.Series],
    cov_matrix: Union[np.ndarray, pd.DataFrame]
) -> pd.Series:
    """
    Calculates % Risk Contribution for each asset.
    RC_i = CVaR_i / Total VaR
    """
    cvar = calculate_component_var(weights, cov_matrix)
    total_var = cvar.sum()
    if abs(total_var) < 1e-9:
        return pd.Series(np.zeros_like(cvar))
    return cvar / total_var
