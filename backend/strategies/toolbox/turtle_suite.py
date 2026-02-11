from typing import Dict, Any
from backend.domain.toolbox.base import BaseSovereignTool
from backend.strategies.turtle import TurtleLegacyStrategy
# Assuming PortfolioManager is a dependency we can mock or inject
from backend.domain.portfolio.manager import PortfolioManager

class TurtleNCalculator(BaseSovereignTool):
    @property
    def name(self) -> str: return "Turtle N-Calc"
    @property
    def category(self) -> str: return "Strategy"
    @property
    def description(self) -> str: return "Calculates 20-day N (ATR) with EMA smoothing."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {highs: [], lows: [], closes: []}
        """
        # Instantiate strategy wrapper just for math
        strat = TurtleLegacyStrategy(PortfolioManager([]))

        import pandas as pd
        highs = pd.Series(data.get("highs", []))
        lows = pd.Series(data.get("lows", []))
        closes = pd.Series(data.get("closes", []))

        n_val = strat.calculate_N(highs, lows, closes)
        return {"N": n_val}

class TurtlePyramiding(BaseSovereignTool):
    @property
    def name(self) -> str: return "Turtle Pyramiding"
    @property
    def category(self) -> str: return "Strategy"
    @property
    def description(self) -> str: return "Manages Unit additions at 0.5N intervals."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {current_price, entry_price, N, current_units}
        """
        price = data.get("current_price")
        entry = data.get("entry_price")
        n = data.get("N")
        units = data.get("current_units", 0)

        # Check if next unit trigger reached (Entry + 0.5 * N * Units) ?
        # Actually Turtle adds at Entry + 1N, +2N? No, usually +0.5N or +1N.
        # Standard: Add unit every 0.5N rise.

        next_entry = entry + (0.5 * n * units)
        signal = "HOLD"
        if price >= next_entry + (0.5 * n): # Trigger for next unit
             signal = "ADD_UNIT"

        return {"signal": signal, "next_entry_trigger": next_entry + (0.5 * n)}

class TurtleStopLoss(BaseSovereignTool):
    @property
    def name(self) -> str: return "Turtle 2N Stop"
    @property
    def category(self) -> str: return "Risk"
    @property
    def description(self) -> str: return "Calculates Hard Stop at Entry - 2N."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        entry = data.get("entry_price")
        n = data.get("N")
        side = data.get("side", "LONG")

        # logic from TurtleStrategy
        if side == "LONG":
            stop = entry - (2 * n)
        else:
            stop = entry + (2 * n)

        return {"stop_price": stop}
