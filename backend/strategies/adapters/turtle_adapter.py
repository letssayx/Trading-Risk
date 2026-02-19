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

            # Initialize N with provided data
            # Calculate ATR (N)
            # Turtle uses 20-day N
            # We need to compute it properly here because calculate_N might need more context or specific Series structure
            # Let's ensure we pass Series with matching index if needed, but list conversion above drops index.
            # Re-creating Series.
            self.strategy.calculate_N(
                pd.Series(self.highs),
                pd.Series(self.lows),
                pd.Series(self.closes)
            )

            # --- LOGIC UPDATE: Use Real Data for Signal ---
            # Donchian Breakout Logic:
            # Buy if Close > Max(High of last 20 days)
            # Sell if Close < Min(Low of last 20 days)

            if len(self.closes) >= 21:
                # Look at previous 20 days (excluding today/current candle)
                # If historical data includes today, use -21:-1.
                # If only closed candles, use -20:.
                # Assuming historical_data is closed candles.

                high_20 = max(self.highs[-21:-1])
                low_20 = min(self.lows[-21:-1])
                current = self.closes[-1]

                if current > high_20:
                    self.signal = "BUY"
                    # Add unit for risk calc
                    self.strategy.add_unit(current, "LONG")
                    # Calculate position size based on 1% risk and N
                    # Unit = (1% of Account) / (N * DollarVolAdjust)
                    # DollarVolAdjust approx 1 for stocks if price is raw
                    self.position = self.strategy.calculate_unit_size(1.0)

                elif current < low_20:
                    self.signal = "SELL"
                    self.strategy.add_unit(current, "SHORT")
                    self.position = self.strategy.calculate_unit_size(1.0)
                else:
                    self.signal = "WAIT"
                    self.position = 0
            else:
                self.signal = "WAIT - INSUFFICIENT DATA"


    def update(self, price: float):
        if not self.is_active: return

        self.last_price = price

        # Real-time Stop Check only
        # No random signals!

        if self.position > 0:
            risk_status = self.strategy.get_risk_status()
            stop = risk_status.get("Current_Stop", 0)

            # Simple Long Stop Check
            if self.signal == "BUY" and price < stop and stop > 0:
                self.signal = "STOP LOSS"
                self.position = 0
                self.strategy.units = 0
                self.strategy.stops = []

            # Simple Short Stop Check
            if self.signal == "SELL" and price > stop and stop > 0:
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
