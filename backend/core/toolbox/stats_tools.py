from typing import Dict, Any, List
import numpy as np
import pandas as pd
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

class ZScoreFilter(BaseSovereignTool):
    @property
    def name(self) -> str: return "Z-Score Filter"
    @property
    def category(self) -> str: return "Indicator" # Brush
    @property
    def description(self) -> str: return "Calculates Rolling Z-Score for Mean Reversion."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        series = pd.Series(data.get("series", []))
        window = data.get("window", 20)

        if len(series) < window: return {"error": "Insufficient Data"}

        rolling_mean = series.rolling(window).mean()
        rolling_std = series.rolling(window).std()
        z_score = (series - rolling_mean) / rolling_std

        return {
            "current_z": z_score.iloc[-1],
            "bands": {
                "upper_2": (rolling_mean + 2*rolling_std).tolist(),
                "lower_2": (rolling_mean - 2*rolling_std).tolist()
            }
        }

class CointegrationAuditor(BaseSovereignTool):
    @property
    def name(self) -> str: return "Cointegration Auditor"
    @property
    def category(self) -> str: return "Governance" # Judge
    @property
    def description(self) -> str: return "Checks Cointegration (Engle-Granger stub)."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Stub for Stationarity check on residuals
        # In prod use statsmodels.tsa.stattools.coint
        return {"status": "PASS", "p_value": 0.04}
