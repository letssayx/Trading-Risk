import sys
import os
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.infrastructure.registry import ToolboxRegistry

def run_sovereign_tests():
    print("Starting Sovereign Workbench Verification...")

    # 1. Registry Auto-Discovery of New Tools
    print("\n--- Testing Registry Auto-Discovery ---")
    ToolboxRegistry.auto_discover()
    tools = ToolboxRegistry.get_all_tools()
    tool_names = [t['name'] for t in tools]
    print(f"Discovered Tools: {tool_names}")

    expected = ["Data Gateway", "Turtle N-Calc", "Factor Exposure Model", "Governance Auditor"]
    for e in expected:
        assert e in tool_names, f"Missing Tool: {e}"
    print("Registry Discovery Verified.")

    # 2. Turtle N-Calc Execution
    print("\n--- Testing Turtle N-Calc ---")
    n_tool = ToolboxRegistry.get_tool("Turtle N-Calc")
    # Mock OHLC
    data = {
        "highs": [105, 106, 107, 108]*10,
        "lows": [100, 101, 102, 103]*10,
        "closes": [102, 103, 104, 105]*10
    }
    res = n_tool.calculate(data)
    print(f"N Result: {res}")
    assert res['N'] > 0, "N calculation failed"

    # 3. Factor Model Execution
    print("\n--- Testing Factor Exposure Model ---")
    factor_tool = ToolboxRegistry.get_tool("Factor Exposure Model")
    # Mock Matrix (Time x Assets) -> 3 assets, 10 periods
    matrix = np.random.randn(20, 3).tolist()
    res_factor = factor_tool.calculate({"returns_matrix": matrix})
    print(f"Factor Result: {res_factor}")
    assert len(res_factor['eigenvalues']) == 3

    # 4. Data Gateway
    print("\n--- Testing Data Gateway ---")
    gw_tool = ToolboxRegistry.get_tool("Data Gateway")
    res_conn = gw_tool.calculate({"action": "CHECK_CONNECTION"})
    print(f"Gateway Status: {res_conn}")
    assert res_conn['status'] == "CONNECTED"

    # Price adjust
    res_adj = gw_tool.calculate({"action": "ADJUST_PRICE", "ticker": "AAPL", "raw_price": 100, "date": "2024-01-01"})
    print(f"Price Adjust: {res_adj}")
    assert 'adjusted_price' in res_adj

    print("\n[SUCCESS] Sovereign Workbench Architecture Verified.")

if __name__ == "__main__":
    run_sovereign_tests()
