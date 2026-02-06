from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseDataProvider(ABC):
    """
    Abstract Adapter for Data Providers (Upstox, Refinitiv, Mock).
    """

    @abstractmethod
    def get_option_chain(self, symbol: str, expiry_date: str) -> Dict[str, Any]:
        """
        Fetches option chain data.
        """
        pass

    @abstractmethod
    def get_historical_ohlc(self, symbol: str, start_date: str, end_date: str) -> Any:
        """
        Fetches historical data.
        """
        pass
