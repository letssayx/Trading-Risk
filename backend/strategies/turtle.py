import pandas as pd
from typing import List, Dict
from backend.domain.portfolio.manager import PortfolioManager

class TurtleLegacyStrategy:
    """
    Implements the Turtle Trading Rules (1983) for Position Sizing and Stops.
    """

    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio_manager = portfolio_manager
        self.N: float = 0.0 # 20-day Average True Range
        self.tick_value: float = 1.0 # Default, should be updated per instrument
        self.units: int = 0
        self.entry_prices: List[float] = [] # List of entry prices for pyramiding
        self.stops: List[float] = [] # List of stop prices corresponding to units

    def calculate_true_range(self, high: float, low: float, prev_close: float) -> float:
        """
        Calculates True Range (TR) = Max(H-L, H-PDC, PDC-L)
        """
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(prev_close - low)
        return max(tr1, tr2, tr3)

    def calculate_N(self, highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 20) -> float:
        """
        Calculates N (ATR) using the 20-day EMA of TR.
        Initial N = SMA of TR for first 20 days.
        Subsequent N = (19 * Prev_N + TR) / 20.
        """
        if len(closes) < period + 1:
            return 0.0

        tr_list = []
        for i in range(1, len(closes)):
            tr = self.calculate_true_range(highs.iloc[i], lows.iloc[i], closes.iloc[i-1])
            tr_list.append(tr)

        tr_series = pd.Series(tr_list)

        # Initial calculation: SMA
        initial_N = tr_series[:period].mean()

        # Subsequent calculation: (19 * Prev + TR) / 20
        # We only need the latest N, but for correctness let's iterate or use pandas ewm
        # The Turtle rule is explicit: N = (19 * PDN + TR) / 20
        # This is equivalent to EMA with alpha = 1/20

        current_N = initial_N
        for i in range(period, len(tr_series)):
            current_N = (19 * current_N + tr_series.iloc[i]) / 20

        self.N = current_N
        return current_N

    def calculate_unit_size(self, tick_value: float) -> int:
        """
        Calculates Unit Size (Contracts) based on 1% risk.
        Unit = (0.01 * Total_Capital) / (N * Tick_Value)
        """
        total_capital = self.portfolio_manager.get_total_capital()
        if self.N <= 0 or tick_value <= 0:
            return 0

        dollar_volatility = self.N * tick_value
        unit_risk = 0.01 * total_capital

        unit_size = int(unit_risk / dollar_volatility)
        return unit_size

    def calculate_stop_price(self, entry_price: float, side: str = "LONG") -> float:
        """
        Calculates initial Hard Stop: Entry - 2N (for Long)
        """
        if self.N <= 0:
            return entry_price # Fallback

        if side.upper() == "LONG":
            return entry_price - (2 * self.N)
        else:
            return entry_price + (2 * self.N)

    def add_unit(self, price: float, side: str = "LONG"):
        """
        Adds a unit (pyramiding) and updates stops.
        If a new unit is added (e.g., at 0.5N profit), move ALL stops to 2N from NEW entry.
        """
        if self.N <= 0:
            return

        # Add new unit
        self.entry_prices.append(price)
        self.units += 1

        # Calculate new stop based on latest entry
        new_stop = self.calculate_stop_price(price, side)

        # Update ALL stops to this new level
        self.stops = [new_stop] * self.units

    def get_risk_status(self) -> Dict[str, float]:
        """
        Returns N, Current Stop, and Risk Exposure.
        """
        if not self.stops:
            current_stop = 0.0
        else:
            current_stop = self.stops[-1]

        return {
            "N": self.N,
            "Current_Stop": current_stop,
            "Units": self.units,
            "Capital_At_Risk_Pct": (self.units * (self.N * self.tick_value)) / self.portfolio_manager.get_total_capital() * 100 if self.portfolio_manager.get_total_capital() > 0 else 0.0
        }
