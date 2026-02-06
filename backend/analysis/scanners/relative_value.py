import pandas as pd

class PairsEngine:
    """
    Calculates RV spread Z-Score for pairs.
    """
    def analyze_spread(self, series_a: pd.Series, series_b: pd.Series) -> float:
        spread = series_a - series_b
        return (spread.iloc[-1] - spread.mean()) / spread.std()
