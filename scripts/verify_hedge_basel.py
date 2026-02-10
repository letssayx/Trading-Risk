import sys
import os
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.analysis.beta import calculate_beta
from backend.risk.hedging import calculate_index_hedge, calculate_sentiment_hedge
from backend.risk.measures.basel import (
    calculate_historical_var,
    calculate_parametric_var,
    calculate_var_se,
    calibrate_stress_period,
    calculate_stressed_var,
    calculate_stressed_es
)
from backend.risk.measures.validation import check_precision_drift
from backend.risk.reports.alpha import generate_alpha_report

def run_tests():
    print("Starting Hedge & Basel Verification...")

    # 1. Beta & Hedging
    print("\n--- Testing Beta & Hedging ---")
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=300)
    market = pd.Series(np.random.normal(0, 0.01, 300), index=dates)
    asset = market * 1.5 + np.random.normal(0, 0.005, 300) # Beta ~ 1.5

    beta = calculate_beta(asset, market, window=252)
    print(f"Calculated Beta: {beta:.4f}")
    assert abs(beta - 1.5) < 0.2, f"Expected Beta ~ 1.5, got {beta}"

    # Index Hedge
    notional = {"AssetA": 1000000}
    betas = {"AssetA": 1.5}
    # Index = 20000, Lot = 50 -> Contract Val = 1M
    hedge_res = calculate_index_hedge(betas, notional, 20000, 50)
    print(f"Hedge Result: {hedge_res}")
    # Exposure = 1.5M. Contract = 1M. Need 1.5 lots.
    assert abs(hedge_res['lots_to_hedge'] - 1.5) < 0.1, "Hedge calculation incorrect"

    # Sentiment Adjustment
    # FII Sell (-100Cr), PCR High (1.6), TRIN High (1.3)
    # Base 10 contracts. +20% (FII) -> 12.
    sent_res = calculate_sentiment_hedge(10, -100, 1.6, 1.3)
    print(f"Sentiment Hedge: {sent_res}")
    assert sent_res['adjusted_contracts'] >= 12, "Sentiment adjustment failed"

    print("Hedging Logic Validated.")

    # 2. Basel VaR & SE
    print("\n--- Testing Basel VaR (n=500) & SE ---")
    # Generate 600 days
    dates_long = pd.date_range('2022-01-01', periods=600)
    returns = pd.Series(np.random.normal(0, 0.01, 600), index=dates_long)

    var_param, sigma = calculate_parametric_var(returns, lookback=500)
    var_se = calculate_var_se(sigma, n=500)

    print(f"Parametric VaR: {var_param:.5f}, Sigma: {sigma:.5f}, SE: {var_se:.5f}")

    # Check SE formula: sigma * sqrt( (1 + 1.645^2/2) / 500 )
    # term = 1 + 2.706/2 = 2.353
    # sqrt(2.353/500) = sqrt(0.0047) = 0.068
    # SE should be approx 0.068 * sigma
    expected_se_ratio = np.sqrt((1 + 1.645**2/2)/500)
    assert abs(var_se/sigma - expected_se_ratio) < 0.01, "SE Calculation mismatch"

    # Precision Check
    # Breach exactly at VaR + 0.5*SE -> Drift
    drift_res = check_precision_drift(- (var_param + 0.5*var_se), var_param, var_se)
    print(f"Drift Check (VaR+0.5SE): {drift_res}")
    assert drift_res == "Precision Drift", "Expected Precision Drift"

    fail_res = check_precision_drift(- (var_param + 2.0*var_se), var_param, var_se)
    print(f"Fail Check (VaR+2SE): {fail_res}")
    assert fail_res == "Hard Breach", "Expected Hard Breach"

    print("Basel VaR Logic Validated.")

    # 3. Stressed Risk Suite
    print("\n--- Testing Stressed Risk Suite ---")
    # Inject a high vol period in the middle
    returns_stress = returns.copy()
    stress_start = 100
    stress_end = 351 # 251 days
    returns_stress.iloc[stress_start:stress_end] = np.random.normal(0, 0.03, stress_end-stress_start) # 3x vol

    stress_window, date_found = calibrate_stress_period(returns_stress)
    print(f"Stress Period Found Ending: {date_found}")

    svar = calculate_stressed_var(stress_window)
    ses = calculate_stressed_es(stress_window)

    print(f"SVaR: {svar:.5f}, SES: {ses:.5f}")

    # SVaR (3x vol) should be much higher than normal VaR
    assert svar > var_param * 2, "Stressed VaR should be significantly higher"
    assert ses > svar, "SES should be > SVaR"

    print("Stressed Risk Logic Validated.")

    # 4. Reporting
    print("\n--- Testing Alpha Report ---")
    summary = {"total_nav": 1e6, "daily_pnl": 1000, "daily_return": 0.001}
    risk = {
        "VaR_95": 15000, "VaR_SE": 1000, "LRcc_decision": "ACCEPTED",
        "SVaR_95": 40000, "SES_95": 50000, "Stress_Period": "2023-Mid"
    }
    attr = {"factor_contributions": {"Mkt": 0.5}}

    report = generate_alpha_report(summary, risk, attr)
    print(report)

    assert "VaR Standard Error" in report
    assert "Stressed VaR (SVaR)" in report
    assert "Regime Divergence" in report # 40k > 1.5 * 15k

    print("Report Integration Validated.")

if __name__ == "__main__":
    run_tests()
