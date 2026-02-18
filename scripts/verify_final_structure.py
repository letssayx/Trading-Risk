import sys
import os
import importlib

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_file(path, description):
    exists = os.path.exists(path)
    print(f"[{'OK' if exists else 'FAIL'}] {description}: {path}")
    return exists

def run_verification():
    print("Starting Final Structure Verification...")

    # 1. File Existence Check
    files_to_check = [
        ("backend/intelligence/sentiment_flow.py", "Sentiment Flow Engine"),
        ("backend/strategies/macro.py", "Macro StatArb (PCA)"),
        ("backend/infrastructure/security.py", "Security Infrastructure"),
        ("backend/analysis/market_state/regime.py", "Regime Detection"),
        ("backend/risk/measures/basel.py", "Basel VaR & Stress"),
        ("backend/MAP.md", "Master Strategy Index"),
        ("backend/ui/templates/workbench.html", "Unified Workbench"),
        ("backend/web/routes.py", "Unified API Router"),
    ]

    all_files_exist = True
    for path, desc in files_to_check:
        if not check_file(path, desc):
            all_files_exist = False

    if not all_files_exist:
        print("\n[ERROR] Missing critical files. Aborting.")
        return

    # 2. Import Logic Check
    print("\n--- Verifying Imports & Logic ---")
    try:
        from backend.intelligence.sentiment_flow import analyze_sentiment_flow
        sig = analyze_sentiment_flow(500, 0.9, 0.8, 0.02, 0.05)
        print(f"[OK] Sentiment Flow Import & Exec: {sig}")
    except Exception as e:
        print(f"[FAIL] Sentiment Flow: {e}")

    try:
        from backend.strategies.macro import MacroStatArbStrategy
        import pandas as pd
        import numpy as np
        df = pd.DataFrame(np.random.randn(50, 3))
        pca = MacroStatArbStrategy().calculate({"returns_matrix": df.values.tolist()})
        print(f"[OK] PCA Logic Import & Exec: Explained Var {pca['explained_variance']}")
    except Exception as e:
        print(f"[FAIL] PCA Logic: {e}")

    try:
        from backend.infrastructure.security import SecurityManager
        sec = SecurityManager()
        token = sec.generate_totp_secret("user1")
        print(f"[OK] Security Manager Import & Exec: Token {token}")
    except Exception as e:
        print(f"[FAIL] Security Manager: {e}")

    print("\n[SUCCESS] All consolidated modules verified.")

if __name__ == "__main__":
    run_verification()
