import pandas as pd
from typing import Any

class Indicator:
    """Base class for all Indicators (Sensors)."""
    def compute(self, data: pd.DataFrame) -> Any:
        raise NotImplementedError

class PriceScanner(Indicator):
    """
    Calculates percentage price change.
    """
    def compute(self, data: pd.DataFrame) -> float:
        # Expects 'close' column
        if len(data) < 2: return 0.0
        return data['close'].pct_change().iloc[-1]

class OIScanner(Indicator):
    """
    Calculates Open Interest percentage change.
    """
    def compute(self, data: pd.DataFrame) -> float:
        # Expects 'oi' column
        if len(data) < 2: return 0.0
        return data['oi'].pct_change().iloc[-1]

class VolumeScanner(Indicator):
    """
    Tracks Delivery % vs 5-day Mean.
    """
    def compute(self, data: pd.DataFrame) -> float:
        # Expects 'delivery_pct'
        if 'delivery_pct' not in data.columns or len(data) < 5: return 0.0
        avg_5 = data['delivery_pct'].rolling(5).mean().iloc[-1]
        current = data['delivery_pct'].iloc[-1]
        return current - avg_5 # Deviation
