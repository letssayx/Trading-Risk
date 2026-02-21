from typing import Dict, Any, List
import numpy as np
from backend.domain.toolbox.base import BaseSovereignTool

class VolArbitrageStrategy(BaseSovereignTool):
    """
    Volatility Arbitrage Strategy: Calendar Spreads & Skew.
    """
    @property
    def name(self) -> str: return "Vol Arbitrage Strategy"
    @property
    def category(self) -> str: return "Strategy"
    @property
    def description(self) -> str: return "Exploits Term Structure and Skew Mispricing."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {iv_near, iv_far}
        """
        iv_near = data.get("iv_near", 0.0)
        iv_far = data.get("iv_far", 0.0)

        spread = iv_near - iv_far
        ratio = iv_near / iv_far if iv_far > 0 else 0

        signal = "NEUTRAL"
        if ratio > 1.15:
            signal = "SHORT_CALENDAR_OPP" # Backwardation: Sell expensive front
        elif ratio < 0.85:
            signal = "LONG_CALENDAR_OPP" # Contango: Buy cheap front? No, Long Cal usually means Long Far.
            # If Front is cheap, maybe Long Front?
            # Standard: Long Calendar = Long Far, Short Near.
            # Ideally enter when Front IV is low relative to Back.

        return {
            "spread": spread,
            "ratio": ratio,
            "signal": signal,
            "strategy": "Calendar Spread"
        }
