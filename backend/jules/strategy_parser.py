from typing import Dict, List, Any
import re

class StrategyParser:
    """
    Parses natural language into strategy configuration and generates Python code.
    Deterministic MVP based on keywords.
    """

    def parse(self, text: str) -> Dict[str, Any]:
        text = text.lower()
        config = {
            "strategy": "custom",
            "filters": [],
            "risk": []
        }

        # 1. Detect Strategy Type
        if "turtle" in text:
            config["strategy"] = "turtle"
            config["params"] = {"entry": 20, "exit": 10}
        elif "mean reversion" in text or "bollinger" in text:
            config["strategy"] = "mean_reversion"
            config["params"] = {"window": 20, "std_dev": 2}
        elif "statarb" in text or "stat arb" in text:
            config["strategy"] = "stat_arb"

        # 2. Detect Filters
        if "z-score" in text or "zscore" in text:
            config["filters"].append({"type": "zscore", "window": 20, "threshold": 2.0})

        if "atr" in text:
            config["filters"].append({"type": "atr", "period": 14})

        if "rsi" in text:
            config["filters"].append({"type": "rsi", "period": 14, "threshold": 70})

        # 3. Detect Risk Models
        if "var" in text:
            config["risk"].append({"type": "var", "confidence": 0.95})

        return config

    def generate_code(self, config: Dict[str, Any]) -> str:
        imports = []
        setup = []

        # Strategy Setup
        strat_type = config.get("strategy")
        if strat_type == "turtle":
            imports.append("from backend.strategies.turtle import TurtleLegacyStrategy")
            setup.append("strategy = TurtleLegacyStrategy(")
            setup.append(f"    entry_period={config.get('params', {}).get('entry', 20)},")
            setup.append(f"    exit_period={config.get('params', {}).get('exit', 10)}")
        elif strat_type == "mean_reversion":
            imports.append("from backend.strategies.mean_reversion import MeanReversionStrategy") # Mock
            setup.append("strategy = MeanReversionStrategy(")
            setup.append(f"    window={config.get('params', {}).get('window', 20)}")
        else:
            imports.append("from backend.strategies.base import BaseStrategy")
            setup.append("strategy = BaseStrategy(")

        # Filters
        filters = config.get("filters", [])
        if filters:
            imports.append("from backend.strategies.toolbox.filters import ZScoreFilter, ATRFilter, RSIFilter") # Mock path
            setup.append(",\n    filters=[")
            for f in filters:
                if f["type"] == "zscore":
                    setup.append(f"        ZScoreFilter(window={f['window']}, threshold={f['threshold']}),")
                elif f["type"] == "atr":
                    setup.append(f"        ATRFilter(period={f['period']}),")
            setup.append("    ]")

        # Risk
        risk = config.get("risk", [])
        if risk:
            imports.append("from backend.risk.measures.var import VaRCalculator")
            setup.append(",\n    risk_checks=[")
            for r in risk:
                if r["type"] == "var":
                    setup.append(f"        VaRCalculator(confidence={r['confidence']}),")
            setup.append("    ]")

        setup.append(")")

        # Execution Stub
        setup.append("\n# Preview on chart")
        setup.append('strategy.run(symbol="NIFTY", data=context["data"])')

        return "\n".join(imports) + "\n\n" + "\n".join(setup)
