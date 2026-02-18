import uuid
import pandas as pd
import numpy as np
import random

class StatArbAdapter:
    def __init__(self, symbol1: str, symbol2: str, ratio: float = 1.0, z_threshold: float = 2.0):
        self.id = str(uuid.uuid4())
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.ratio = ratio
        self.z_threshold = z_threshold
        self.is_active = False

        self.last_spread = 0.0
        self.z_score = 0.0
        self.mean = 0.0
        self.std = 0.0
        self.signal = "WAIT"

    def start(self, historical_spread: list):
        self.is_active = True

        # Calculate mean/std from history
        values = [d['value'] for d in historical_spread]
        if values:
            self.mean = np.mean(values)
            self.std = np.std(values)
            self.last_spread = values[-1]
            self.update_z_score()

    def update(self, price1: float, price2: float):
        if not self.is_active: return

        # Calculate new spread
        self.last_spread = price1 - (self.ratio * price2)

        # Update rolling stats (Simplified: just using historical mean/std, maybe slight drift)
        # In real StatArb, we'd update rolling window.

        self.update_z_score()

        # Generate Signal
        if self.z_score > self.z_threshold:
            self.signal = "SHORT SPREAD" # Sell 1, Buy 2
        elif self.z_score < -self.z_threshold:
            self.signal = "LONG SPREAD" # Buy 1, Sell 2
        elif abs(self.z_score) < 0.5:
            self.signal = "EXIT"
        else:
            self.signal = "HOLD"

    def update_z_score(self):
        if self.std > 0:
            self.z_score = (self.last_spread - self.mean) / self.std
        else:
            self.z_score = 0.0

    def get_state(self):
        return {
            "id": self.id,
            "symbol1": self.symbol1,
            "symbol2": self.symbol2,
            "spread": round(self.last_spread, 2),
            "z_score": round(self.z_score, 2),
            "signal": self.signal,
            "active": self.is_active
        }
