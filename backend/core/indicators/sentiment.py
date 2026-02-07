from backend.core.indicators.technical import Indicator
import pandas as pd

class InstitutionalSentiment(Indicator):
    """
    Calculates FII Long/Short Ratio.
    Formula: Ratio = FII_Long / FII_Short
    """
    def compute(self, data: pd.DataFrame) -> float:
        # Expects 'fii_long', 'fii_short'
        latest = data.iloc[-1]
        short = latest.get('fii_short', 0)
        if short == 0: return 0.0
        return latest.get('fii_long', 0) / short
