import sys
import os
import json
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.intelligence.toolbox.rubric import ScoringService
from backend.risk.toolbox.measures import calculate_historical_var
from backend.strategies.toolbox.library import StrategyLibrary

def run_toolbox_tests():
    print("Starting Toolbox Verification...")

    # 1. Scoring Service (Rubric)
    print("\n--- Testing Scoring Service ---")
    scorer = ScoringService() # Default weights
    metrics = {
        "sharpe_ratio": 1.5, # > 1.0 -> Max Score contribution
        "sortino_ratio": 2.0,
        "governance_status": "ACCEPTED"
    }
    score_res = scorer.calculate_score(metrics)
    print(f"Score Result: {score_res}")

    # Sharpe 1.5 -> Score = min(1.5*50, 100) = 75. Contrib = 75 * 0.4 = 30.
    # Sortino 2.0 -> Score = min(2.0*40, 100) = 80. Contrib = 80 * 0.3 = 24.
    # Governance -> 100 * 0.3 = 30.
    # Total = 30 + 24 + 30 = 84. Grade A.

    assert score_res["total_score"] == 84.0
    assert score_res["grade"] == "A"

    # 2. Risk Toolbox (Pure Functions)
    print("\n--- Testing Risk Toolbox ---")
    data = pd.Series(np.random.normal(0, 0.01, 100))
    var = calculate_historical_var(data, lookback=50)
    print(f"Toolbox VaR: {var:.5f}")
    assert var > 0

    # 3. Strategy Toolbox (OOTB Library)
    print("\n--- Testing Strategy Library ---")
    turtle = StrategyLibrary.get_turtle_strategy(capital=500000.0)
    print(f"Turtle Strategy Initialized. Capital: {turtle.portfolio_manager.get_total_capital()}")
    assert turtle.portfolio_manager.get_total_capital() == 500000.0

    # 4. Defaults Config
    print("\n--- Testing OOTB Defaults ---")
    risk_conf_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'config', 'defaults', 'risk.json')
    with open(risk_conf_path, 'r') as f:
        risk_conf = json.load(f)
        print(f"Risk Defaults: {risk_conf}")
        assert risk_conf["basel_lookback_days"] == 500

    print("\n[SUCCESS] Toolbox Architecture Verified.")

if __name__ == "__main__":
    run_toolbox_tests()
