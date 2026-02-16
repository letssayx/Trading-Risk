from typing import Dict, Any, List
import pandas as pd
from backend.strategies.turtle import TurtleLegacyStrategy

class TurtleAdapter:
    """
    Stateful adapter for Turtle Strategy on a single symbol.
    Maintains rolling history for N calculation.
    """
    def __init__(self, symbol: str, lookback: int = 20):
        self.symbol = symbol
        self.lookback = lookback
        self.history: List[float] = [] # Price history
        self.strategy = TurtleLegacyStrategy(entry_period=lookback, exit_period=int(lookback/2))

    def update(self, price: float) -> Dict[str, Any]:
        """
        Updates state with new price and returns strategy metrics.
        """
        self.history.append(price)
        # Keep buffer just enough for N calc + safety
        if len(self.history) > self.lookback * 2:
            self.history = self.history[-self.lookback*2:]

        # Convert to OHLC-like dataframe for the strategy
        # Strategy expects 'close', 'high', 'low'
        # We simulate candles from ticks (or just use close) for MVP
        df = pd.DataFrame({'close': self.history, 'high': self.history, 'low': self.history})

        # Calculate N (ATR)
        # We need to manually invoke logic or trust the strategy to handle series
        # TurtleLegacyStrategy.run expects a dataframe and returns signals

        # For efficiency, we might just calculate N directly here or use a helper
        # but let's try to use the sovereign tool if possible.

        # Simulating N calculation for MVP robustness without full DF dependency overhead per tick
        # True Range = max(high-low, abs(high-close_prev), abs(low-close_prev))
        # Since we only have close price ticks, TR is essentially change from prev close?
        # No, that's not right for Turtle.
        # Ideally we feed it Daily OHLC.
        # ADAPTER ASSUMPTION: 'price' is the latest EOD or live tick.
        # We will calc simple Volatility if high/low missing.

        n_val = df['close'].diff().abs().rolling(window=self.lookback).mean().iloc[-1] if len(df) > self.lookback else 0.0

        # Generate Signal (Breakout)
        # Buy if > max(last 20)
        # Sell if < min(last 20)
        upper = df['close'].rolling(window=self.lookback).max().iloc[-2] if len(df) > 1 else price
        lower = df['close'].rolling(window=self.lookback).min().iloc[-2] if len(df) > 1 else price

        signal = "HOLD"
        if price > upper: signal = "BUY"
        elif price < lower: signal = "SELL"

        # Stop Loss (2N)
        stop = price - (2 * n_val) if signal == "BUY" else price + (2 * n_val)

        return {
            "symbol": self.symbol,
            "price": price,
            "n": round(n_val, 2),
            "signal": signal,
            "stop": round(stop, 2),
            "size": int(10000 / (n_val * 1)) if n_val > 0 else 0 # 10k risk / dollar vol
        }
