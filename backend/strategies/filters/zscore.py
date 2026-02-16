import pandas as pd
from typing import Dict, Any, Union
from backend.domain.toolbox.base import BaseSovereignTool

class ZScoreFilter(BaseSovereignTool):
    """
    Computes Z-Score of a time series.
    Returns signal if |z| > threshold.
    """
    @property
    def name(self) -> str: return "Z-Score Filter"
    @property
    def category(self) -> str: return "Filter"
    @property
    def description(self) -> str: return "Standardized deviation from mean."

    def __init__(self, window: int = 20, threshold: float = 2.0):
        self.window = window
        self.threshold = threshold

    def calculate(self, data: Union[pd.Series, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Expects data as pd.Series or Dict with 'close' prices.
        """
        if isinstance(data, dict):
            # Assume it's a dict with price history list
            series = pd.Series(data.get("prices", []))
        else:
            series = data

        if len(series) < self.window:
            return {"z_score": 0.0, "signal": 0}

        rolling_mean = series.rolling(window=self.window).mean()
        rolling_std = series.rolling(window=self.window).std()

        current_val = series.iloc[-1]
        mu = rolling_mean.iloc[-1]
        sigma = rolling_std.iloc[-1]

        if sigma == 0:
            return {"z_score": 0.0, "signal": 0}

        z = (current_val - mu) / sigma

        signal = 0
        if z > self.threshold: signal = -1 # Mean reversion: Sell
        elif z < -self.threshold: signal = 1 # Mean reversion: Buy

        return {
            "z_score": z,
            "mean": mu,
            "std": sigma,
            "signal": signal
        }
