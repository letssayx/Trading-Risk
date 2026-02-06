# Comprehensive Import Check for MVP Build
# This script attempts to import all key components to ensure syntax validity and proper structure.

import sys
import os

# Add root to python path to emulate running from root
sys.path.append(os.getcwd())

def verify_mvp_build():
    print("Verifying MVP Build Integration...")

    try:
        # Phase 1: Data & Domain
        from backend.domain.models import Instrument, MarketData, Strategy, Trade, RiskSnapshot
        from backend.data.adapter import BaseDataProvider
        from backend.data.upstox import UpstoxProvider
        from backend.data.mock import MockProvider
        print("✅ Phase 1 (Data & Domain) - Models & Providers OK")

        # Phase 2: Logic & Blueprints
        from backend.strategies.base_strategy import BaseStrategy
        from backend.strategies.engine import StrategyEngine
        # Verify StrategyRunner logic existence (it's inside StrategyEngine class)
        print("✅ Phase 2 (Logic) - BaseStrategy & StrategyEngine OK")

        # Phase 3: Quantitative Suite
        from backend.analysis.scanners.relative_value import PairsEngine
        from backend.risk.measures.var import calculate_parametric_var, aggregate_greeks
        from backend.risk.scenarios.generator import ScenarioGenerator
        from backend.risk.manager import RiskManager
        print("✅ Phase 3 (Quant Suite) - Scanners, VaR, & RiskManager OK")

        # Phase 4: AI Orchestration
        from backend.orchestration.gemini_orchestrator import GeminiOrchestrator
        from backend.orchestration.strategy_manager import save_natural_language_strategy
        print("✅ Phase 4 (AI Orchestration) - Gemini & StrategyManager OK")

        # Phase 5: Web/API (Optional Check)
        from backend.widgets.routes import get_widget_data
        print("✅ Phase 5 (API) - Widget Routes OK")

        print("\n🏆 Turtle Terminal MVP Build Verification: PASSED")

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        exit(1)
    except SyntaxError as e:
        print(f"\n❌ Syntax Error: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Runtime Error: {e}")
        exit(1)

if __name__ == "__main__":
    verify_mvp_build()
