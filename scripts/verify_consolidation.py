import sys
import os
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from new consolidated locations
from backend.strategies.macro_stat_arb import calculate_pca_factors
from backend.strategies.vol_arb import calculate_vol_spread
from backend.strategies.convergence import check_convergence
from backend.intelligence.sentiment_flow import analyze_sentiment_flow
from backend.analysis.market_state.sectors import map_sector_classification
from backend.analysis.greeks import interpret_iv_skew
from backend.risk.reports.alpha import generate_alpha_report

def run_consolidation_test():
    print("Starting Institutional Consolidation Verification...")

    # 1. Macro StatArb (PCA)
    print("\n--- Testing Macro StatArb (PCA) ---")
    np.random.seed(42)
    # 3 Assets, 100 days
    data = np.random.normal(0, 0.01, (100, 3))
    df = pd.DataFrame(data, columns=['A', 'B', 'C'])
    pca_res = calculate_pca_factors(df, n_components=2)
    print(f"Explained Variance: {pca_res['explained_variance']}")
    assert len(pca_res['eigenvalues']) == 2, "PCA should return 2 components"

    # 2. Vol Arbitrage (Calendar Spread)
    print("\n--- Testing Vol Arbitrage ---")
    # Backwardation: Near 30%, Far 20% -> Ratio 1.5 -> Short Calendar
    vol_res = calculate_vol_spread(0.30, 0.20)
    print(f"Vol Spread Result: {vol_res}")
    assert vol_res['signal'] == "SHORT_CALENDAR_OPP", "Expected Short Calendar Signal"

    # 3. Intelligence Core (Sentiment & Sectors)
    print("\n--- Testing Intelligence Core ---")
    sector = map_sector_classification("RELIANCE")
    print(f"RELIANCE Sector: {sector}")
    assert sector == "Oil & Gas", "Sector mapping failed"

    sent_sig = analyze_sentiment_flow(500, 0.9, 0.8, 0.02, 0.05)
    print(f"Sentiment Signal: {sent_sig}")
    assert sent_sig == "BUY", "Sentiment Analysis failed"

    skew_res = interpret_iv_skew(0.20, 0.25, 0.22) # Put Skew
    print(f"IV Skew: {skew_res}")
    assert skew_res['skew_type'] == "NEUTRAL", "Expected Neutral (diff 0.05 < 2.0)"
    # Wait, input logic: 0.25 - 0.20 = 0.05. Code checks > 2.0 (absolute value or percentage points?)
    # Usually IV is percentage e.g. 25.0 vs 20.0. Here used 0.25.
    # Let's test with percentage points: 25.0, 20.0 -> diff 5.0 > 2.0
    skew_res_pct = interpret_iv_skew(20.0, 25.0, 22.0)
    print(f"IV Skew (Pct): {skew_res_pct}")
    assert skew_res_pct['skew_type'] == "PUT_SKEW", "Expected Put Skew"

    # 4. Generate Alpha Report (Data Pipe Check)
    print("\n--- Generating Alpha Report ---")
    summary = {"total_nav": 1e6, "daily_pnl": 2000}
    risk = {"VaR_95": 10000, "SVaR_95": 15000}
    attr = {"factor_contributions": {"PCA_1": 0.5}}

    report = generate_alpha_report(summary, risk, attr)
    print(report)
    assert "Stressed VaR" in report

    print("\n[SUCCESS] Turtle Master Index Implementation Verified.")

if __name__ == "__main__":
    run_consolidation_test()
