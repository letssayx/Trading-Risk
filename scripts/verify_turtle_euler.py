import sys
import os
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.strategies.turtle import TurtleLegacyStrategy
from backend.domain.portfolio.manager import PortfolioManager
from backend.risk.manager import RiskManager

def run_tests():
    print("Starting Turtle & Euler Verification...")

    # 1. Verify Turtle Logic
    print("\n--- Testing Turtle Strategy ---")
    pm = PortfolioManager(trades=[], total_capital=1_000_000.0)
    strategy = TurtleLegacyStrategy(portfolio_manager=pm)

    # Create dummy data (25 days)
    # Price oscillating around 100 with range ~2
    dates = pd.date_range('2023-01-01', periods=25)
    closes = pd.Series([100 + np.sin(i)*2 for i in range(25)], index=dates)
    highs = closes + 1.0
    lows = closes - 1.0

    # Calculate N
    n_val = strategy.calculate_N(highs, lows, closes, period=20)
    print(f"Calculated N (20-day): {n_val}")

    # Expected approximate N: Range is ~2. SMA ~2.
    # TR = H-L = 2. N should be close to 2.
    assert abs(n_val - 2.0) < 0.5, f"Expected N ~ 2.0, got {n_val}"

    # Unit Size
    # Capital 1M, N ~2, Tick Value 50 (e.g. ES futures)
    # Unit Risk = 10,000
    # Dollar Vol = 2 * 50 = 100
    # Unit Size = 10,000 / 100 = 100 contracts

    # Use fixed N for deterministic test
    strategy.N = 2.0
    unit_size = strategy.calculate_unit_size(tick_value=50.0)
    print(f"Unit Size (N=2.0, Tick=50): {unit_size}")
    assert unit_size == 100, f"Expected 100 units, got {unit_size}"

    # Stop Logic
    # Entry 100, N 2 -> Stop 96 (Long)
    stop = strategy.calculate_stop_price(entry_price=100.0, side="LONG")
    print(f"Stop Price (Entry=100, N=2, Long): {stop}")
    assert stop == 96.0, f"Expected stop 96.0, got {stop}"

    # Pyramiding
    # Add unit at 101 (+0.5N). New Stop should be 101 - 2N = 97.
    strategy.add_unit(101.0, side="LONG")
    print(f"New Stop after Pyramiding (Entry=101): {strategy.stops[-1]}")
    assert strategy.stops[-1] == 97.0, f"Expected new stop 97.0, got {strategy.stops[-1]}"

    print("Turtle Logic Validated.")

    # 2. Verify Euler Risk Manager
    print("\n--- Testing Euler Risk Manager ---")
    rm = RiskManager()

    # 3 Assets
    assets = ['A', 'B', 'C']
    weights = pd.Series([0.5, 0.3, 0.2], index=assets)
    # Simple Covariance (Diagonal)
    cov = pd.DataFrame(np.diag([0.04, 0.04, 0.04]), index=assets, columns=assets)

    # MVaR should be proportional to weight * vol
    # Vol = 0.2
    # MVaR_A ~ 0.5 * 0.2 = 0.1? No.
    # Total Var = w'Cw = 0.5^2*0.04 + 0.3^2*0.04 + 0.2^2*0.04 = 0.04*(0.25+0.09+0.04) = 0.04*0.38 = 0.0152
    # Total Vol = sqrt(0.0152) = 0.123
    # MVaR_A = (Cov*w)_A / Vol * Z
    # (Cov*w)_A = 0.04 * 0.5 = 0.02
    # MVaR_A = 0.02 / 0.123 * 1.645 (Z_95) = 0.162 * 1.645 = 0.26
    # CVaR_A = 0.5 * 0.26 = 0.13

    # Budgets: Equal Risk (1/3 each)
    budgets = pd.Series([0.33, 0.33, 0.33], index=assets)

    imbalances = rm.check_risk_imbalance(weights, cov, risk_budgets=budgets, threshold=0.15)

    print("Imbalances found:", imbalances)
    # Asset A has 50% weight, equal vol. Contribution ~ 50%^2 / sum(w^2) ? No.
    # Contribution is w_i * (Cw)_i / Var
    # RC_A = 0.5 * (0.04*0.5) / 0.0152 = 0.01 / 0.0152 = 0.65 (65%)
    # Budget 33%. 65% > 33% * 1.15 (38%). So Imbalanced.

    assert 'A' in imbalances, "Asset A should be flagged as imbalanced"

    # Suggestions
    suggested = rm.suggest_risk_balanced_weights(cov, risk_budgets=budgets)
    print("Suggested Weights:", suggested)

    # Should be equal weights (0.33 each) since vols are equal and correlations 0
    assert np.isclose(suggested['A'], 0.333, atol=0.05), f"Expected ~0.33, got {suggested['A']}"

    print("Euler Risk Manager Validated.")

if __name__ == "__main__":
    run_tests()
