from backend.strategies.base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, Any

class PairsTrading(BaseStrategy):
    """
    Standard Cointegration/Z-Score Mean Reversion.
    """
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Simplified: We assume 'close' represents the Spread/Ratio directly for this MVP plugin
        # In full system, this would receive two series.
        window = self.config.get("lookback", 20)
        df['spread_mean'] = df['close'].rolling(window=window).mean()
        df['spread_std'] = df['close'].rolling(window=window).std()
        df['z_score'] = (df['close'] - df['spread_mean']) / df['spread_std']
        return df

    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        z = df.iloc[-1]['z_score']
        entry = self.config.get("entry_z", 2.0)
        exit_z = self.config.get("exit_z", 0.0)

        if z > entry:
            return "SHORT_SPREAD"
        elif z < -entry:
            return "LONG_SPREAD"
        elif abs(z) < exit_z:
            return "EXIT"
        return "HOLD"

    def youtube(self) -> None:
        pass
