import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class UpstoxClient:
    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("UPSTOX_ACCESS_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def validate_token(self) -> bool:
        if not self.is_configured():
            return False
        try:
            # Simple profile check to validate token
            res = requests.get(f"{self.BASE_URL}/user/profile", headers=self.headers, timeout=5)
            return res.status_code == 200
        except:
            return False

    def get_historical_candles(self, instrument_key: str, interval: str, to_date: str, from_date: str) -> List[Dict]:
        """
        Fetch historical candles.
        interval: '1minute', '30minute', 'day', etc.
        """
        if not self.is_configured():
            return []

        url = f"{self.BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json().get("data", {}).get("candles", [])
                # Upstox returns [[timestamp, open, high, low, close, volume, oi], ...]
                candles = []
                for row in data:
                    candles.append({
                        "time": row[0],
                        "open": row[1],
                        "high": row[2],
                        "low": row[3],
                        "close": row[4],
                        "volume": row[5],
                        "oi": row[6] if len(row) > 6 else 0
                    })
                # Sort by time ascending
                candles.sort(key=lambda x: x["time"])
                return candles
            else:
                print(f"Upstox Error ({res.status_code}): {res.text}")
                return []
        except Exception as e:
            print(f"Upstox Exception: {e}")
            return []

    def get_market_quote(self, instrument_keys: List[str]) -> Dict[str, Any]:
        """
        Get live market quotes (LTP, OHLC, etc.)
        """
        if not self.is_configured():
            return {}

        url = f"{self.BASE_URL}/market-quote/quotes"
        params = {"instrument_key": ",".join(instrument_keys)}
        try:
            res = requests.get(url, headers=self.headers, params=params, timeout=5)
            if res.status_code == 200:
                return res.json().get("data", {})
            return {}
        except Exception as e:
            print(f"Upstox Quote Exception: {e}")
            return {}

    def search_instrument(self, query: str) -> List[Dict]:
        """
        Search for an instrument to get its key.
        Using a public instrument file or search API if available.
        Upstox doesn't have a simple search API in v2 free tier sometimes,
        but let's try assuming standard endpoint or we map standard symbols.
        Actually, we might need to map 'RELIANCE' to 'NSE_EQ|INE002A01018'.
        For now, let's assume we use a mapping or search.
        """
        # Search is complex without the full instrument dump.
        # Fallback: Assume NSE_EQ|{Symbol} for stocks.
        return []

    def get_instrument_key(self, symbol: str, exchange: str = "NSE_EQ") -> str:
        # Simple heuristic mapping
        # In real app, we'd lookup in a database of instruments
        return f"{exchange}|{symbol}"

# Singleton
upstox_client = UpstoxClient()
