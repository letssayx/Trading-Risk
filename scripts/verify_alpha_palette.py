import sys
import os
import pandas as pd
import numpy as np

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.infrastructure.registry import ToolboxRegistry

def run_alpha_palette_tests():
    print("Starting Alpha Palette Verification...")

    # 1. Registry Discovery
    print("\n--- Testing Registry Auto-Discovery ---")
    ToolboxRegistry.auto_discover()
    tools = ToolboxRegistry.get_all_tools()
    tool_names = [t['name'] for t in tools]
    print(f"Discovered: {tool_names}")

    expected = ["Spread Synthesizer", "FICO Tool", "Z-Score Filter", "Cointegration Auditor"]
    for e in expected:
        assert e in tool_names, f"Missing {e}"

    print("Registry Verified.")

    # 2. Spread Synthesizer
    print("\n--- Testing Spread Synthesizer ---")
    spread_tool = ToolboxRegistry.get_tool("Spread Synthesizer")
    sa = [100, 102, 104, 106]
    sb = [50, 51, 52, 53]
    # Ratio 2.0 -> Spread = A - 2B = 100-100=0, 102-102=0...
    res = spread_tool.calculate({"series_a": sa, "series_b": sb, "ratio": 2.0})
    print(f"Spread Result: {res}")
    assert res['current_value'] == 0

    # 3. FICO Tool
    print("\n--- Testing FICO Tool ---")
    fico = ToolboxRegistry.get_tool("FICO Tool")
    # Perfect correlation
    res_fico = fico.calculate({"series_a": sa, "series_b": sb})
    print(f"FICO Result: {res_fico}")
    assert res_fico['correlation'] > 0.99

    print("\n[SUCCESS] Alpha Palette Architecture Verified.")

if __name__ == "__main__":
    run_alpha_palette_tests()
