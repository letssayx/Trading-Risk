from backend.strategies.base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, Any

class CrossMarketScreener(BaseStrategy):
    """
    Alpha Signals combining Cash Delivery and Derivatives Data.
    """
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Expected cols: 'close', 'oi', 'delivery_pct'

        if 'delivery_pct' in df.columns:
            df['avg_delivery_5'] = df['delivery_pct'].rolling(5).mean()
            df['delivery_spike'] = df['delivery_pct'] > (df['avg_delivery_5'] * 1.2) # 20% above mean

        if 'oi' in df.columns:
            df['oi_chg'] = df['oi'].pct_change()
            df['long_buildup'] = (df['close'].pct_change() > 0) & (df['oi_chg'] > 0.05)

        return df

    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        latest = df.iloc[-1]

        # SIGNAL 1: Accumulation (Price Up + OI Up + High Delivery)
        acc = latest.get('long_buildup', False) and latest.get('delivery_spike', False)

        if acc:
            return "ACCUMULATION_BUY"

        # SIGNAL 2: Insti-Flow (Mock check if FII Cash Net > 0)
        # In real system, pass 'fii_cash_net' in df or context

        return "NEUTRAL"

    def youtube(self) -> None:
        pass
