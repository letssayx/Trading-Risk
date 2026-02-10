import sys
import os
import numpy as np
import pandas as pd

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.risk.measures.optimization import calculate_marginal_var, calculate_component_var, calculate_risk_contributions
from backend.risk.measures.attribution import calculate_factor_attribution
from backend.risk.measures.validation import kupiec_pof_test
from backend.risk.reports.alpha import generate_alpha_report

def run_tests():
    print("Starting Verification...")

    # 1. Test Euler Optimization (MVaR, CVaR)
    print("\n--- Testing Euler Optimization ---")
    weights = pd.Series([0.4, 0.6], index=['AssetA', 'AssetB'])
    cov = pd.DataFrame([[0.04, 0.01], [0.01, 0.09]], index=['AssetA', 'AssetB'], columns=['AssetA', 'AssetB'])

    mvar = calculate_marginal_var(weights, cov)
    cvar = calculate_component_var(weights, cov)
    rc = calculate_risk_contributions(weights, cov)

    print(f"Weights: {weights.values}")
    print(f"MVaR: {mvar.values}")
    print(f"CVaR: {cvar.values}")
    print(f"Total VaR (Sum CVaR): {cvar.sum()}")
    print(f"Risk Contributions: {rc.values}")

    # Validate Sum CVaR = Total VaR
    # Total Var = sqrt(w'Cw) * Z
    from scipy.stats import norm
    z = norm.ppf(0.95)
    total_std = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    expected_var = total_std * z
    # Note: calculate_marginal_var uses alpha=0.05 by default (95% conf)

    assert np.isclose(cvar.sum(), expected_var), f"Expected {expected_var}, got {cvar.sum()}"
    print("Euler Decomposition Validated.")

    # 2. Test Factor Attribution
    print("\n--- Testing Factor Attribution ---")
    dates = pd.date_range('2023-01-01', periods=100)
    market = np.random.normal(0.0005, 0.01, 100) # Market factor
    sector = np.random.normal(0.0002, 0.02, 100) # Sector factor
    factors = pd.DataFrame({'Market': market, 'Sector': sector}, index=dates)

    # Generate portfolio returns: Rp = 0.8*M + 0.5*S + noise
    noise = np.random.normal(0, 0.005, 100)
    port_ret = 0.8 * market + 0.5 * sector + 0.0001 + noise # Alpha 0.0001 daily
    port_ret_series = pd.Series(port_ret, index=dates)

    attrib = calculate_factor_attribution(port_ret_series, factors)
    print(f"Betas: {attrib['betas'].values}")
    print(f"Alpha (Ann): {attrib['alpha']}")
    print(f"R-Squared: {attrib['r_squared']}")

    # Check if betas are close to 0.8 and 0.5
    betas = attrib['betas']
    assert abs(betas['Market'] - 0.8) < 0.25, f"Expected Market Beta ~0.8, got {betas['Market']}"
    assert abs(betas['Sector'] - 0.5) < 0.25, f"Expected Sector Beta ~0.5, got {betas['Sector']}"
    print("Attribution Validated.")

    # 3. Test Kupiec POF
    print("\n--- Testing Kupiec POF ---")
    # Failures = 6, Observations = 100, Confidence = 0.95 (Expected failures = 5)
    lr, p_val, decision = kupiec_pof_test(6, 100, 0.95)
    print(f"Failures: 6/100, Conf: 0.95 -> LR: {lr:.4f}, p-val: {p_val:.4f}, Decision: {decision}")

    # Failures = 20, Observations = 100, Confidence = 0.95 (Expected 5) -> Should Reject
    lr_bad, p_bad, dec_bad = kupiec_pof_test(20, 100, 0.95)
    print(f"Failures: 20/100, Conf: 0.95 -> LR: {lr_bad:.4f}, p-val: {p_bad:.4f}, Decision: {dec_bad}")
    assert dec_bad == "Reject", "Kupiec test failed to reject bad model."
    print("Kupiec Test Validated.")

    # 4. Test Alpha Report
    print("\n--- Testing Alpha Report ---")
    # Mock data
    summary = {"total_nav": 1000000, "daily_pnl": 5000, "daily_return": 0.005}
    risk = {"VaR_95": 15000, "top_risk_contributors": {"AAPL": 0.4, "GOOG": 0.3}}
    attr = {"factor_contributions": attrib['contributions'].to_dict(), "residual_return": 0.002}

    report = generate_alpha_report(summary, risk, attr)
    print(report)
    print("Report Generation Validated.")

if __name__ == "__main__":
    run_tests()
