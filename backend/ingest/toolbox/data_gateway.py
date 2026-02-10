from typing import Dict, Any, List
from datetime import datetime
from backend.domain.toolbox.base import BaseSovereignTool
from backend.ingest.adjustment import PriceAdjuster

class DataGateway(BaseSovereignTool):
    """
    Sovereign Tool for Data Ingestion and Adjustment.
    Wraps PriceAdjuster and Connectivity Checks.
    """
    @property
    def name(self) -> str: return "Data Gateway"
    @property
    def category(self) -> str: return "Ingest"
    @property
    def description(self) -> str: return "Handles Upstox Connectivity and Corporate Action Adjustments."

    def __init__(self):
        self.adjuster = PriceAdjuster()

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {"action": "ADJUST_PRICE", "ticker": "AAPL", "raw_price": 150.0, "date": "2023-01-01"}
        OR {"action": "CHECK_CONNECTION"}
        """
        action = data.get("action")

        if action == "CHECK_CONNECTION":
            # Mock connectivity check
            return {"status": "CONNECTED", "latency_ms": 45}

        if action == "ADJUST_PRICE":
            ticker = data.get("ticker")
            raw = data.get("raw_price")
            date_str = data.get("date")
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                adj_price = self.adjuster.get_adjusted_price(ticker, raw, date)
                return {"adjusted_price": adj_price}
            except Exception as e:
                return {"error": str(e)}

        return {"error": "Unknown Action"}
