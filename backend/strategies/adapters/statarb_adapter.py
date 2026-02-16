from typing import Dict, Any, List
import pandas as pd
import numpy as np
from backend.strategies.stat_arb.alpha_engine import StatArbAlphaEngine

class StatArbAdapter:
    """
    Stateful adapter for Pairs Trading.
    Maintains history for two symbols.
    """
    def __init__(self, sym1: str, sym2: str, lookback: int = 20):
        self.sym1 = sym1
        self.sym2 = sym2
        self.history1: List[float] = []
        self.history2: List[float] = []
        self.lookback = lookback
        self.engine = StatArbAlphaEngine()

    def update(self, price1: float, price2: float) -> Dict[str, Any]:
        self.history1.append(price1)
        self.history2.append(price2)

        # Trim
        if len(self.history1) > self.lookback * 2:
            self.history1 = self.history1[-self.lookback*2:]
            self.history2 = self.history2[-self.lookback*2:]

        if len(self.history1) < self.lookback:
            return {
                "sym1": self.sym1, "sym2": self.sym2,
                "p1": price1, "p2": price2,
                "spread": 0.0, "z_score": 0.0, "signal": "WAIT"
            }

        # Calc Spread & Z-Score
        # Simple ratio or diff? Engine likely uses OLS or log diff.
        # Let's use simple diff for MVP adapter speed.
        s1 = pd.Series(self.history1)
        s2 = pd.Series(self.history2)

        # Hedge Ratio (simple regression)
        # beta = cov(s1,s2) / var(s2)
        # spread = s1 - beta * s2
        # For MVP: Spread = s1 - s2 (assuming similar notional or pre-adjusted)
        spread_series = s1 - s2

        current_spread = spread_series.iloc[-1]
        mean = spread_series.rolling(window=self.lookback).mean().iloc[-1]
        std = spread_series.rolling(window=self.lookback).std().iloc[-1]

        z = (current_spread - mean) / std if std != 0 else 0

        signal = "HOLD"
        if z > 2.0: signal = "SHORT" # Spread too high, Sell 1 Buy 2
        elif z < -2.0: signal = "LONG" # Spread too low, Buy 1 Sell 2
        elif abs(z) < 0.5: signal = "EXIT"

        return {
            "sym1": self.sym1, "sym2": self.sym2,
            "p1": price1, "p2": price2,
            "spread": round(current_spread, 2),
            "z_score": round(z, 2),
            "signal": signal
        }
