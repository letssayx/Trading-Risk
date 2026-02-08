from datetime import datetime
from typing import Dict, List

class PriceAdjuster:
    """
    Handles corporate actions adjustments (splits, bonuses) for historical data.
    Ensures backtests don't show false PnL due to price drops from splits.
    """
    def __init__(self):
        # In a real system, this would load from a corporate actions database
        # Structure: {ticker: [{date, type, ratio}, ...]}
        self.corporate_actions: Dict[str, List[Dict]] = {}

    def add_split(self, ticker: str, date: datetime, ratio: float):
        """
        Ratio: e.g., 10 for a 10:1 split (1 share becomes 10).
        Price drops by factor of 10.
        """
        if ticker not in self.corporate_actions:
            self.corporate_actions[ticker] = []
        self.corporate_actions[ticker].append({"type": "SPLIT", "date": date, "ratio": ratio})

    def get_adjusted_price(self, ticker: str, raw_price: float, date: datetime) -> float:
        """
        Adjusts historical price to be comparable to current price (Forward Adjustment).
        Alternatively, standard practice is Backward Adjustment: old prices are lowered.

        If split 10:1 happened on 2024-01-01 (Ratio 10):
        - Date 2023-12-31: Raw Price 2000 -> Adjusted 200.
        - Date 2024-01-02: Raw Price 200 -> Adjusted 200.

        So if date < action.date, divide by ratio.
        """
        actions = self.corporate_actions.get(ticker, [])
        adjusted_price = raw_price

        for action in actions:
            if action["type"] == "SPLIT" and date < action["date"]:
                adjusted_price = adjusted_price / action["ratio"]
            elif action["type"] == "BONUS" and date < action["date"]:
                # Bonus 1:1 means ratio 2 (1 share becomes 2)
                adjusted_price = adjusted_price / action["ratio"]

        return adjusted_price
