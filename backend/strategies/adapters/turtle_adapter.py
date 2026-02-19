import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Dict, Optional
from backend.strategies.turtle import TurtleLegacyStrategy
from backend.domain.portfolio.manager import PortfolioManager
from backend.domain.market.models import Bhavcopy
from backend.domain.market.contract_manager import ContractManager

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
        self.segment = "CM" # Default
        self.expiry_position = 1 # Default Near Month (FUT1)
        self.current_contract_symbol = None
        self.last_oi = 0
        self.last_volume = 0

        # Simulation state
        self.highs = []
        self.lows = []
        self.closes = []
        self.signal = "WAIT"

    def set_config(self, segment: str, expiry_pos: int = 1):
        self.segment = segment
        self.expiry_position = expiry_pos

    def start(self, historical_data: List[dict]):
        self.is_active = True

        # Parse historical data to initialize N
        import pandas as pd
        df = pd.DataFrame(historical_data)
        if not df.empty:
            self.highs = df['high'].tolist()
            self.lows = df['low'].tolist()
            self.closes = df['close'].tolist()
            self.last_price = self.closes[-1]

            # Capture metadata from last candle
            last_candle = df.iloc[-1]
            self.current_contract_symbol = last_candle.get('symbol', self.symbol)
            self.last_oi = last_candle.get('oi', 0)
            self.last_volume = last_candle.get('volume', 0)

            # Initialize N
            self.strategy.calculate_N(
                pd.Series(self.highs),
                pd.Series(self.lows),
                pd.Series(self.closes)
            )

            # Check Signal (Donchian 20-day)
            if len(self.closes) >= 21:
                high_20 = max(self.highs[-21:-1])
                low_20 = min(self.lows[-21:-1])
                current = self.closes[-1]

                if current > high_20:
                    self.signal = "BUY"
                    self.strategy.add_unit(current, "LONG")
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

        # Stop Checks
        if self.position > 0:
            risk_status = self.strategy.get_risk_status()
            stop = risk_status.get("Current_Stop", 0)

            if self.signal == "BUY" and price < stop and stop > 0:
                self.signal = "STOP LOSS"
                self.position = 0
                self.strategy.units = 0
                self.strategy.stops = []

            if self.signal == "SELL" and price > stop and stop > 0:
                 self.signal = "STOP LOSS"
                 self.position = 0
                 self.strategy.units = 0
                 self.strategy.stops = []

    def get_state(self):
        risk = self.strategy.get_risk_status()
        # Retrieve mapped symbol, OI, Volume from current data if available
        # This requires tracking the last fetched 'contract' or data point details
        # Since 'update' only receives price, we might need to store more metadata
        # For now, we'll try to infer or pass it.
        # Ideally, start() or update() sets these.
        # But start() parses a list. Let's assume start() sets metadata from the last candle.

        # If we want the mapped symbol (e.g. RELIANCE26FEBFUT), we need to have stored it.
        # But fetch_historical_data returns dicts.
        # We need to enhance fetch_historical_data or pass it here.

        # Use captured metadata
        display_sym = self.current_contract_symbol if self.current_contract_symbol else self.symbol

        return {
            "id": self.id,
            "symbol": display_sym, # Shows mapped symbol (e.g. RELIANCE26FEBFUT)
            "segment": self.segment,
            "expiry_pos": self.expiry_position,
            "active": self.is_active,
            "price": self.last_price,
            "n": round(risk.get("N", 0), 2),
            "signal": self.signal,
            "stop": round(risk.get("Current_Stop", 0), 2),
            "position_size": self.position,
            "units": risk.get("Units", 0),
            "oi": self.last_oi,
            "volume": self.last_volume
        }
