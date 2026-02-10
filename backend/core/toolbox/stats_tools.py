import numpy as np
import pandas as pd
from typing import Dict, Any, List
from backend.domain.toolbox.base import BaseSovereignTool

class StatArbAlphaEngine(BaseSovereignTool):
    """
    Detects Mean Reversion and Z-Score Divergence.
    """
    @property
    def name(self) -> str: return "StatArb Alpha Engine"
    @property
    def category(self) -> str: return "Strategy"
    @property
    def description(self) -> str: return "Identifies Z-Score divergence for Pairs Trading."

    def calculate(self, data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        data: {"series_a": [...], "series_b": [...]}
        """
        sa = pd.Series(data.get("series_a", []))
        sb = pd.Series(data.get("series_b", []))

        if len(sa) != len(sb):
            return {"error": "Series length mismatch"}

        # Spread = A - HedgeRatio * B (Simplistic A - B for now)
        spread = sa - sb
        mean = spread.mean()
        std = spread.std()

        z_score = (spread.iloc[-1] - mean) / std if std > 0 else 0

        signal = "NEUTRAL"
        if z_score > 2.0: signal = "SHORT_SPREAD"
        elif z_score < -2.0: signal = "LONG_SPREAD"

        return {
            "z_score": z_score,
            "signal": signal,
            "mean_spread": mean
        }
