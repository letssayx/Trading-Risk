from backend.strategies.base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, Any

class SmartMoneyPulse(BaseStrategy):
    """
    Analyzes Institutional vs Retail Positioning.
    """
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Expected df columns: 'fii_long', 'fii_short', 'client_long', 'client_short'
        # In a real pipeline, these would be joined from ParticipantPosition table.

        if 'fii_long' in df.columns:
            df['fii_ratio'] = df['fii_long'] / df['fii_short'].replace(0, 1)
            df['client_ratio'] = df['client_long'] / df['client_short'].replace(0, 1)

        return df

    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        latest = df.iloc[-1]

        fii_bullish = latest.get('fii_ratio', 1.0) > 1.5
        client_bearish = latest.get('client_ratio', 1.0) < 0.8 # Contrarian

        if fii_bullish and client_bearish:
            return "STRONG_BUY_SIGNAL"
        elif latest.get('fii_ratio', 1.0) < 0.6:
            return "INSTITUTIONAL_EXIT"

        return "NEUTRAL"

    def youtube(self) -> None:
        pass
