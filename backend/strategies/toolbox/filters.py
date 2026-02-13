import pandas as pd
from typing import Dict, Any
from backend.domain.toolbox.base import BaseSovereignTool

class ZScoreFilter(BaseSovereignTool):
    """
    Calculates Rolling Z-Score for Mean Reversion.
    Used to filter trade signals based on statistical divergence.
    """
    @property
    def name(self) -> str: return "Z-Score Filter"
    @property
    def category(self) -> str: return "Indicator"
    @property
    def description(self) -> str: return "Calculates Rolling Z-Score for Mean Reversion."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {"series": [...], "window": 20}
        """
        series = pd.Series(data.get("series", []))
        window = data.get("window", 20)

        if len(series) < window: return {"error": "Insufficient Data"}

        rolling_mean = series.rolling(window).mean()
        rolling_std = series.rolling(window).std()

        if rolling_std.iloc[-1] == 0:
            z_score = 0.0
        else:
            z_score = (series.iloc[-1] - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]

        return {
            "current_z": float(z_score),
            "bands": {
                "upper_2": (rolling_mean + 2*rolling_std).tolist(),
                "lower_2": (rolling_mean - 2*rolling_std).tolist()
            }
        }
