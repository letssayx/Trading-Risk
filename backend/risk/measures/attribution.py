import numpy as np
import pandas as pd
from typing import Dict, Union

def calculate_factor_attribution(
    portfolio_returns: pd.Series,
    factor_returns: pd.DataFrame,
    annualization_factor: int = 252
) -> Dict[str, Union[pd.Series, float]]:
    """
    Performs regression-based factor attribution.
    R_p = alpha + beta * R_f + epsilon

    Args:
        portfolio_returns: Time series of portfolio returns.
        factor_returns: Time series of factor returns (columns are factor names).
        annualization_factor: Factor to scale returns (default 252 for daily).

    Returns:
        Dictionary containing:
        - "betas": Factor sensitivities (coefficients).
        - "contributions": Annualized contribution of each factor (beta * factor_mean * ann_factor).
        - "alpha": Annualized alpha (intercept * ann_factor).
        - "r_squared": R-squared of the regression.
        - "residual_vol": Annualized residual volatility.
    """
    # Align dates
    common_idx = portfolio_returns.index.intersection(factor_returns.index)
    if len(common_idx) < 30: # Require at least 30 data points
        raise ValueError(f"Insufficient overlapping data for regression. Found {len(common_idx)} points.")

    y = portfolio_returns.loc[common_idx].values
    X = factor_returns.loc[common_idx].values

    # Add constant for alpha
    X_with_const = np.column_stack([np.ones(len(X)), X])

    # OLS: beta = (X'X)^-1 X'y
    try:
        # lstsq returns: x, residuals, rank, s
        coeffs, residuals_sum_sq, rank, s = np.linalg.lstsq(X_with_const, y, rcond=None)
    except np.linalg.LinAlgError:
        raise ValueError("Linear regression failed (singular matrix?).")

    alpha = coeffs[0]
    betas = coeffs[1:]

    factor_names = factor_returns.columns
    beta_series = pd.Series(betas, index=factor_names)

    # Calculate Contributions (Annualized)
    # Contribution = Beta * Mean Factor Return * Ann
    factor_means = factor_returns.loc[common_idx].mean()
    contributions = beta_series * factor_means * annualization_factor

    # R-squared
    # TSS = sum((y - mean(y))^2)
    # RSS = sum(residuals^2)
    # R^2 = 1 - RSS/TSS
    y_mean = np.mean(y)
    tss = np.sum((y - y_mean)**2)

    if residuals_sum_sq.size > 0:
        rss = residuals_sum_sq[0]
    else:
        # If perfect fit or something, calculate manually
        y_pred = np.dot(X_with_const, coeffs)
        rss = np.sum((y - y_pred)**2)

    r_squared = 1 - (rss / tss) if tss > 0 else 0.0

    # Residual Volatility (Annualized)
    # Std dev of epsilon
    # DOF = N - k (where k is number of parameters including intercept)
    dof = len(y) - X_with_const.shape[1]
    if dof <= 0:
        residual_std = 0.0
    else:
        residual_std = np.sqrt(rss / dof)

    residual_vol = residual_std * np.sqrt(annualization_factor)

    return {
        "betas": beta_series,
        "contributions": contributions,
        "alpha": alpha * annualization_factor,
        "r_squared": r_squared,
        "residual_vol": residual_vol
    }
