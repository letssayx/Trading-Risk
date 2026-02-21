import uuid
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from backend.strategies.turtle import TurtleLegacyStrategy
from backend.domain.portfolio.manager import PortfolioManager

class MockPortfolioManager(PortfolioManager):
    def __init__(self, capital=1000000.0):
        self.total_capital = capital
        self.trades = []

    def get_total_capital(self) -> float:
        return self.total_capital

class TurtleAdapter:
    def __init__(self, symbol: str, risk_per_trade: float = 0.01):
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.risk_per_trade = risk_per_trade
        self.portfolio = MockPortfolioManager()
        self.strategy = TurtleLegacyStrategy(self.portfolio)
        self.is_active = False
        self.last_price = 0.0
        self.position = 0

        self.highs = []
        self.lows = []
        self.closes = []
        self.signal = "WAIT"

    def start(self, historical_data: List[dict]):
        self.is_active = True

        df = pd.DataFrame(historical_data)
        if not df.empty:
            self.highs = df['high'].tolist()
            self.lows = df['low'].tolist()
            self.closes = df['close'].tolist()
            self.last_price = self.closes[-1]

            # Initialize N
            self.strategy.calculate_N(
                pd.Series(self.highs),
                pd.Series(self.lows),
                pd.Series(self.closes)
            )

            # Check for initial signal
            if len(self.highs) > 20:
                high_20 = max(self.highs[-21:-1])
                if self.closes[-1] > high_20:
                    self.signal = "BUY"
                    # Simple unit size calc
                    self.position = self.strategy.calculate_unit_size(1.0)
                    self.strategy.add_unit(self.closes[-1], "LONG")

            # If no signal, just WAIT
        else:
            # No data
            self.signal = "NO DATA"

    def update(self, price: float):
        if not self.is_active: return

        self.last_price = price

        # Here we would implement real intraday logic:
        # Check if price crosses stop or breakout level.

        if self.position > 0:
            risk_status = self.strategy.get_risk_status()
            stop = risk_status.get("Current_Stop", 0)
            if price < stop:
                self.signal = "STOP LOSS"
                self.position = 0
                self.strategy.units = 0
                self.strategy.stops = []

    def get_state(self):
        risk = self.strategy.get_risk_status()
        return {
            "id": self.id,
            "symbol": self.symbol,
            "active": self.is_active,
            "price": self.last_price,
            "n": round(risk.get("N", 0), 2),
            "signal": self.signal,
            "stop": round(risk.get("Current_Stop", 0), 2),
            "position_size": self.position,
            "units": risk.get("Units", 0)
        }
