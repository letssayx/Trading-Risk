import pandas as pd

class SentimentGauge:
    """
    Calculates PCR Z-Score.
    """
    def compute_z_score(self, current_pcr: float, pcr_history: pd.Series) -> float:
        mean = pcr_history.mean()
        std = pcr_history.std()
        if std == 0: return 0.0
        return (current_pcr - mean) / std
