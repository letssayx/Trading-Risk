from typing import Dict, Any
import pandas as pd
from backend.domain.toolbox.base import BaseSovereignTool

class SpreadSynthesizer(BaseSovereignTool):
    """
    Creates a virtual instrument (A - Ratio * B).
    """
    @property
    def name(self) -> str: return "Spread Synthesizer"
    @property
    def category(self) -> str: return "Math"
    @property
    def description(self) -> str: return "Creates Synthetic Spread (A - B)."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {series_a: [], series_b: [], ratio: 1.0}
        """
        sa = pd.Series(data.get("series_a", []))
        sb = pd.Series(data.get("series_b", []))
        ratio = data.get("ratio", 1.0)

        # Ensure length match (simplified)
        min_len = min(len(sa), len(sb))
        spread = sa[:min_len] - (ratio * sb[:min_len])

        return {
            "spread_series": spread.tolist(),
            "current_value": spread.iloc[-1] if not spread.empty else 0
        }

class FICOTool(BaseSovereignTool):
    """
    Financial Intersection & Correlation (FICO).
    """
    @property
    def name(self) -> str: return "FICO Tool"
    @property
    def category(self) -> str: return "Indicator"
    @property
    def description(self) -> str: return "Calculates Correlation & Cointegration metrics."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sa = pd.Series(data.get("series_a", []))
        sb = pd.Series(data.get("series_b", []))

        if len(sa) != len(sb): return {"error": "Length Mismatch"}

        correlation = sa.corr(sb)

        return {
            "correlation": correlation,
            "interpretation": "High Correlation" if abs(correlation) > 0.8 else "Low/Neutral"
        }
