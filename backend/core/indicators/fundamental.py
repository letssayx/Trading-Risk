from backend.core.indicators.technical import Indicator
import pandas as pd

class FundamentalValue(Indicator):
    """
    Calculates Z-Score of PE Ratio relative to Sector Average.
    """
    def compute(self, data: pd.DataFrame) -> float:
        # Expects 'pe_ratio' series
        if len(data) < 20: return 0.0
        mean = data['pe_ratio'].mean()
        std = data['pe_ratio'].std()
        if std == 0: return 0.0
        current = data['pe_ratio'].iloc[-1]
        return (current - mean) / std
