import numpy as np
from typing import Tuple, Dict

def kupiec_pof_test(
    failures: int,
    observations: int,
    confidence_level: float = 0.95
) -> Tuple[float, float, str]:
    """
    Kupiec's Proportion of Failures (POF) test.
    Tests the null hypothesis that the observed failure rate matches the expected failure rate.

    Args:
        failures: Number of VaR breaches.
        observations: Total number of days in backtest.
        confidence_level: Expected confidence level (e.g., 0.95 or 0.99).

    Returns:
        (lr_stat, p_value, decision)
        decision: "Accept" or "Reject" (at 5% significance level for the test itself).
    """
    from scipy.stats import chi2

    p = 1.0 - confidence_level
    T = observations
    x = failures

    # Handle edge cases
    if T == 0:
        return 0.0, 1.0, "Invalid (T=0)"

    rate = x / T

    # Likelihood Ratio calculation
    # LR = -2 * ln( L_null / L_alt )
    # L_null = (1-p)^(T-x) * p^x
    # L_alt  = (1-rate)^(T-x) * rate^x

    # Use log-likelihoods to avoid underflow
    if x == 0:
        ln_l_alt = 0.0
        ln_l_null = T * np.log(1 - p)
    elif x == T:
         ln_l_alt = 0.0
         ln_l_null = T * np.log(p)
    else:
        ln_l_null = (T - x) * np.log(1 - p) + x * np.log(p)
        ln_l_alt = (T - x) * np.log(1 - rate) + x * np.log(rate)

    lr_stat = -2 * (ln_l_null - ln_l_alt)

    # Chi-square with 1 degree of freedom
    p_value = 1 - chi2.cdf(lr_stat, df=1)

    # Decision at 5% significance
    decision = "Reject" if p_value < 0.05 else "Accept"

    return lr_stat, p_value, decision

def christoffersen_test(
    breaches: np.ndarray
) -> Tuple[float, float, str, Dict[str, int]]:
    """
    Christoffersen's Conditional Coverage Test (LRind).
    Tests for serial independence of breaches (volatility clustering).

    Args:
        breaches: Binary array (1 = breach, 0 = no breach).

    Returns:
        (lr_ind, p_value, decision, transitions)
    """
    from scipy.stats import chi2

    # Create pairs (t, t+1)
    if len(breaches) < 2:
        return 0.0, 1.0, "Insufficient Data", {}

    # Using stride tricks to create sliding window
    pairs = np.lib.stride_tricks.sliding_window_view(breaches, 2)

    # Transition counts
    # T00: No Breach -> No Breach
    T00 = np.sum((pairs[:, 0] == 0) & (pairs[:, 1] == 0))
    # T01: No Breach -> Breach
    T01 = np.sum((pairs[:, 0] == 0) & (pairs[:, 1] == 1))
    # T10: Breach -> No Breach
    T10 = np.sum((pairs[:, 0] == 1) & (pairs[:, 1] == 0))
    # T11: Breach -> Breach
    T11 = np.sum((pairs[:, 0] == 1) & (pairs[:, 1] == 1))

    transitions = {"T00": int(T00), "T01": int(T01), "T10": int(T10), "T11": int(T11)}

    # Probabilities
    # pi0: Prob of breach given no breach
    denom0 = T00 + T01
    pi0 = T01 / denom0 if denom0 > 0 else 0.0

    # pi1: Prob of breach given breach
    denom1 = T10 + T11
    pi1 = T11 / denom1 if denom1 > 0 else 0.0

    # Unconditional probability (independence)
    denom_all = T00 + T01 + T10 + T11
    pi = (T01 + T11) / denom_all if denom_all > 0 else 0.0

    # Log-Likelihoods
    # L_null (Independence): (T00+T10) ln(1-pi) + (T01+T11) ln(pi)
    # L_alt (Markov): T00 ln(1-pi0) + T01 ln(pi0) + T10 ln(1-pi1) + T11 ln(pi1)

    def safe_log(x):
        return np.log(x) if x > 0 else 0.0

    ln_l_null = (T00 + T10) * safe_log(1 - pi) + (T01 + T11) * safe_log(pi)
    ln_l_alt = (T00 * safe_log(1 - pi0) + T01 * safe_log(pi0) +
                T10 * safe_log(1 - pi1) + T11 * safe_log(pi1))

    lr_ind = -2 * (ln_l_null - ln_l_alt)

    # Chi-square with 1 degree of freedom
    p_value = 1 - chi2.cdf(lr_ind, df=1)

    decision = "Reject" if p_value < 0.05 else "Accept"

    return lr_ind, p_value, decision, transitions

def calculate_lr_cc(
    breaches: np.ndarray,
    confidence_level: float = 0.95
) -> Tuple[float, float, str, Dict[str, float]]:
    """
    LR Conditional Coverage (LRcc) = LRpof + LRind.
    Tests both coverage rate and independence.
    Critical Value at 95% (df=2) is 5.99.
    """
    from scipy.stats import chi2

    failures = np.sum(breaches)
    observations = len(breaches)

    lr_pof, p_pof, _ = kupiec_pof_test(failures, observations, confidence_level)
    lr_ind, p_ind, _, transitions = christoffersen_test(breaches)

    lr_cc = lr_pof + lr_ind

    # Chi-square with 2 degrees of freedom
    p_value = 1 - chi2.cdf(lr_cc, df=2)

    # Critical Value Check (5.99 Rule)
    # Reject if LRcc > 5.99 (at 95% confidence)
    decision = "REJECTED" if lr_cc > 5.99 else "ACCEPTED"

    details = {
        "LRpof": lr_pof,
        "LRind": lr_ind,
        "LRcc": lr_cc,
        "transitions": transitions,
        "failures": int(failures),
        "observations": observations
    }

    return lr_cc, p_value, decision, details

def check_precision_drift(
    pnl: float,
    var_threshold: float,
    var_se: float
) -> str:
    """
    Checks if a breach is a 'Hard Breach' or 'Precision Drift'.
    Drift: Breach is within 1x SE of the VaR line.

    Args:
        pnl: Profit/Loss (negative for loss).
        var_threshold: VaR value (positive).
        var_se: Standard Error of VaR (positive).

    Returns:
        Status string: "No Breach", "Precision Drift", "Hard Breach"
    """
    loss = -pnl
    if loss <= var_threshold:
        return "No Breach"

    # Breach occurred. Check magnitude.
    # If Loss <= VaR + SE, it's a Drift.
    if loss <= (var_threshold + var_se):
        return "Precision Drift"
    else:
        return "Hard Breach"
