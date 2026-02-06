from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    """
    Abstract Blueprint for all Turtle Terminal strategies.
    Ensures deterministic logic for indicator math and signal generation.
    """
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Input: OHLCV + Greeks DataFrame.
        Output: DataFrame with new columns for indicators (e.g., 'rsi', 'iv_rank').
        """
        pass

    @abstractmethod
    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        """
        Input: The enriched DataFrame from compute_indicators.
        Output: A signal string: 'BUY', 'SELL', 'EXIT', or 'HOLD'.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.name,
            "parameters": self.config
        }

    @abstractmethod
    def youtube(self) -> None:
        """
        Placeholder for strategy-specific media/logging actions or external hooks.
        As per requirements.
        """
        pass
