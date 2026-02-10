import numpy as np
import pandas as pd
from typing import Tuple, Dict
from scipy.stats import genpareto

def fit_gpd_parameters(exceedances: np.ndarray) -> Tuple[float, float]:
    """
    Fits Generalized Pareto Distribution (GPD) to exceedances over threshold.
    Returns:
        (xi, beta): Shape (xi) and Scale (beta) parameters.
    """
    # Exceedances should be positive (Loss - Threshold)
    if len(exceedances) < 10:
        # Not enough data for reliable EVT
        return 0.0, 0.0

    # Fit GPD
    # genpareto.fit returns (xi, loc, scale). We fix loc=0 for POT on excesses.
    # Note: scipy uses 'c' for shape parameter xi.
    params = genpareto.fit(exceedances, floc=0)
    xi = params[0]
    beta = params[2]

    return xi, beta

def calculate_evt_es(
    losses: np.ndarray,
    confidence_level: float = 0.95,
    threshold_percentile: float = 0.95
) -> Dict[str, float]:
    """
    Calculates EVT-VaR and EVT-ES (Expected Shortfall) using Peaks-Over-Threshold (POT).

    Args:
        losses: Array of historical losses (positive values).
        confidence_level: Target confidence (e.g. 0.99).
        threshold_percentile: Threshold u (e.g. 95th percentile of losses).

    Returns:
        Dictionary with EVT metrics.
    """
    # 1. Determine Threshold u
    u = np.percentile(losses, threshold_percentile * 100)

    # 2. Extract Exceedances
    exceedances = losses[losses > u] - u
    n_u = len(exceedances)
    n = len(losses)

    if n_u < 10:
        return {
            "EVT_VaR": np.nan,
            "EVT_ES": np.nan,
            "xi": 0.0,
            "beta": 0.0,
            "u": u,
            "message": "Insufficient tail data"
        }

    # 3. Fit GPD
    xi, beta = fit_gpd_parameters(exceedances)

    # 4. Calculate EVT-VaR
    # VaR_q = u + (beta/xi) * [ ( (n/n_u) * (1-q) )^(-xi) - 1 ]
    # where q is confidence level (e.g. 0.99)
    # Ensure 1-q is small (e.g. 0.01)

    alpha = 1 - confidence_level
    term1 = (n / n_u) * alpha

    if xi != 0:
        evt_var = u + (beta / xi) * (np.power(term1, -xi) - 1)
    else:
        evt_var = u - beta * np.log(term1)

    # 5. Calculate EVT-ES
    # ES_q = (VaR_q + beta - xi*u) / (1 - xi) ??
    # Formula: ES = VaR / (1-xi) + (beta - xi*u) / (1-xi)
    # Wait, simpler formula given in prompt:
    # ES = VaR / (1-xi) + (beta - xi*u) / (1-xi)
    # Actually, standard formula for GPD ES (mean excess over VaR):
    # E[X-VaR | X>VaR] = (beta + xi*(VaR-u)) / (1-xi)
    # So ES = VaR + MeanExcess
    # Let's stick to prompt formula: "ES = VaR/(1-xi) + (beta - xi*u)/(1-xi)"
    # Note: This assumes specific parameterization. Let's implement exactly as requested.

    if xi < 1:
        evt_es = (evt_var) / (1 - xi) + (beta - xi * u) / (1 - xi)
    else:
        evt_es = np.inf # Mean undefined if xi >= 1

    return {
        "EVT_VaR": evt_var,
        "EVT_ES": evt_es,
        "xi": xi,
        "beta": beta,
        "u": u,
        "exceedances": n_u
    }
