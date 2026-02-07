from backend.core.strategies.base import BaseStrategy
from backend.core.indicators.sentiment import InstitutionalSentiment
import pandas as pd

class SmartMoneyStrategy(BaseStrategy):
    """
    Uses InstitutionalSentiment Indicator to flag Conviction.
    """
    def run(self, data: pd.DataFrame) -> str:
        # data needs 'fii_long', 'fii_short', 'client_long', 'client_short'

        # Inject Indicator logic (if passed in init, or instantiate)
        sentiment_ind = self.indicators.get('sentiment') or InstitutionalSentiment()

        # We need a Client Sentiment indicator too, ideally injected.
        # For refactoring demo, we calc ratios here using indicator pattern

        fii_ratio = sentiment_ind.compute(data)

        # Client Ratio (Inverse) logic inline or via separate indicator
        latest = data.iloc[-1]
        client_ratio = latest.get('client_long', 0) / latest.get('client_short', 1)

        if fii_ratio > 1.5 and client_ratio < 0.8:
            return "STRONG_BUY_SIGNAL"
        elif fii_ratio < 0.6:
            return "INSTITUTIONAL_EXIT"

        return "NEUTRAL"
