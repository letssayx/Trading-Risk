from backend.data.adapter import BaseDataProvider
from typing import Dict, Any
import pandas as pd

class MockProvider(BaseDataProvider):
    """
    Offline Mock Provider for testing.
    """
    def get_option_chain(self, symbol: str, expiry_date: str) -> Dict[str, Any]:
        print(f"⚠️ Using MockProvider for {symbol}")
        mock_data = [
            {"strikePrice": 19500, "CE.openInterest": 200000, "PE.openInterest": 150000, "CE.lastPrice": 150, "PE.lastPrice": 80},
            {"strikePrice": 19600, "CE.openInterest": 250000, "PE.openInterest": 100000, "CE.lastPrice": 100, "PE.lastPrice": 120}
        ]
        return {
            "timestamp": "2026-02-06 15:30:00",
            "underlying": 19550.0,
            "data": pd.DataFrame(mock_data)
        }

    def get_historical_ohlc(self, symbol: str, start_date: str, end_date: str) -> Any:
        return pd.DataFrame()
