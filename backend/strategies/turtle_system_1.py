import pandas as pd
from typing import Dict, Any
from backend.strategies.base_strategy import BaseStrategy
from backend.strategies.indicators import calc_atr, calc_donchian

class TurtleSystem1(BaseStrategy):
    def __init__(self):
        super().__init__("Turtle System 1")
        self.entry_period = 20
        self.exit_period = 10

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Turtle System 1 logic:
        - ATR (N) for sizing (though sizing logic is separate, we compute it).
        - 20-day High for Entry.
        - 10-day Low for Exit.
        """
        df = calc_atr(df, period=20)
        df = calc_donchian(df, period=self.entry_period) # Entry Breakout
        df = calc_donchian(df, period=self.exit_period)  # Exit Breakout
        # Renaming columns for clarity if needed, but calc_donchian uses suffixes
        return df

    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        """
        Returns signal based on current price vs channels.
        """
        if df.empty:
            return "HOLD"

        last_row = df.iloc[-1]
        price = last_row['close']

        # Channel values
        entry_high = last_row[f'High_{self.entry_period}']
        exit_low = last_row[f'Low_{self.exit_period}']

        # Position check
        is_long = current_pos.get('quantity', 0) > 0

        if not is_long:
            # Entry Rule: Price > 20-Day High
            # (Strictly: Close > High, or Intraday Breakout)
            if price > entry_high:
                return "BUY"
        else:
            # Exit Rule: Price < 10-Day Low
            if price < exit_low:
                return "EXIT"

        return "HOLD"
