import sys
import os
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.analysis.sentiment import analyze_sentiment_flow
from backend.web.strategies.convergence import check_convergence
from backend.web.strategies.risk import get_risk_dashboard_data
from backend.risk.reports.alpha import generate_alpha_report

def run_tests():
    print("Starting Strategy Convergence & Dashboard Verification...")

    # 1. Sentiment Flow
    print("\n--- Testing Sentiment Flow ---")
    # Case: FII Buy, PCR < 0.8 (Wait, logic said > 0.8), Price Up, OI Up -> BUY
    # Logic in code: "If PCR > 0.8: return BUY"
    signal_buy = analyze_sentiment_flow(fii_net_cash=500, pcr=0.9, trin=0.8, price_change=0.02, oi_change=0.05)
    print(f"Sentiment Signal (FII+, PCR 0.9, Price+, OI+): {signal_buy}")
    assert signal_buy == "BUY", "Expected BUY signal"

    # Case: FII Sell, TRIN > 1.2, Price Down, OI Up -> SELL
    signal_sell = analyze_sentiment_flow(fii_net_cash=-500, pcr=1.0, trin=1.5, price_change=-0.02, oi_change=0.05)
    print(f"Sentiment Signal (FII-, TRIN 1.5, Price-, OI+): {signal_sell}")
    assert signal_sell == "SELL", "Expected SELL signal"

    print("Sentiment Flow Validated.")

    # 2. Convergence Logic
    print("\n--- Testing Convergence ---")
    conv_high = check_convergence("BUY", "BUY")
    print(f"Convergence (Buy, Buy): {conv_high}")
    assert conv_high["status"] == "HIGH_CONVICTION", "Expected HIGH_CONVICTION"

    conv_conflict = check_convergence("BUY", "SELL")
    print(f"Convergence (Buy, Sell): {conv_conflict}")
    assert conv_conflict["status"] == "CONFLICT", "Expected CONFLICT"

    conv_mod = check_convergence("NEUTRAL", "SELL")
    print(f"Convergence (Neutral, Sell): {conv_mod}")
    assert conv_mod["status"] == "MODERATE", "Expected MODERATE"

    print("Convergence Logic Validated.")

    # 3. Risk Dashboard Data
    print("\n--- Testing Risk Dashboard Data ---")
    # Beta 1.5, Market +1% -> Drag +1.5%
    # VaR 10k, SE 1k -> Band 9k-11k
    risk_data = get_risk_dashboard_data(portfolio_beta=1.5, market_return=0.01, var_95=10000, var_se=1000)
    print(f"Risk Dashboard: {risk_data}")

    assert risk_data["nifty_drag_pct"] == 0.015, "Expected 1.5% Beta Drag"
    assert risk_data["var_confidence_band"]["upper"] == 11000, "Expected Upper VaR 11k"
    assert risk_data["precision_status"] == "STABLE", "Expected Stable Precision"

    print("Risk Dashboard Logic Validated.")

    # 4. Report with Split
    print("\n--- Testing Alpha Report Split ---")
    summary = {"total_nav": 1e6, "daily_pnl": 5000}
    risk = {"VaR_95": 10000}
    attr = {"strategy_pnl": {"Turtle": 3000, "Sentiment": 2000, "Hedge": -500}}

    report = generate_alpha_report(summary, risk, attr)
    print(report)

    assert "STRATEGY PERFORMANCE SPLIT" in report
    assert "- Turtle: $3,000.00" in report

    print("Report Integration Validated.")

if __name__ == "__main__":
    run_tests()
