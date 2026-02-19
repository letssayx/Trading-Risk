import uuid
import pandas as pd
import numpy as np
from datetime import datetime
import random
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

        # Simulation state
        self.highs = []
        self.lows = []
        self.closes = []
        self.signal = "WAIT"

    def start(self, historical_data: List[dict]):
        self.is_active = True

        # Parse historical data to initialize N
        df = pd.DataFrame(historical_data)
        if not df.empty:
            self.highs = df['high'].tolist()
            self.lows = df['low'].tolist()
            self.closes = df['close'].tolist()
            self.last_price = self.closes[-1]

            # Initialize N
            # We need Series for the strategy method
            self.strategy.calculate_N(
                pd.Series(self.highs),
                pd.Series(self.lows),
                pd.Series(self.closes)
            )

            # Check for initial signal (Mock: Breakout of 20-day high)
            if len(self.highs) > 20:
                high_20 = max(self.highs[-21:-1])
                if self.closes[-1] > high_20:
                    self.signal = "BUY"
                    self.position = self.strategy.calculate_unit_size(1.0) # Tick value 1
                    self.strategy.add_unit(self.closes[-1], "LONG")

    def update(self, price: float):
        if not self.is_active: return

        self.last_price = price
        # Update N (Mock update: assume price is close of a new candle for simplicity,
        # or just decay/drift N slightly to show life)
        # Real turtle updates N daily. Intraday we watch price vs levels.

        # Check stops
        if self.position > 0:
            risk_status = self.strategy.get_risk_status()
            stop = risk_status.get("Current_Stop", 0)
            if price < stop:
                self.signal = "STOP LOSS"
                self.position = 0
                self.strategy.units = 0
                self.strategy.stops = []

        # Simple random signal flip for demo if idle
        if self.signal == "WAIT" and random.random() > 0.95:
             self.signal = "BUY" if random.random() > 0.5 else "SELL"
             self.position = self.strategy.calculate_unit_size(1.0)
             self.strategy.add_unit(price, "LONG" if self.signal == "BUY" else "SHORT")

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
