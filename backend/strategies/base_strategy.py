from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators like ATR, Highs, Lows."""
        pass

    @abstractmethod
    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        """Return 'BUY', 'SELL', 'EXIT', or 'HOLD'."""
        pass

    @abstractmethod
    def youtube(self) -> None:
        """
        Placeholder for strategy-specific media/logging actions or external hooks.
        As per requirements.
        """
        pass
