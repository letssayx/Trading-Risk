from typing import Dict, Any

class RolloverAnalyzer:
    """
    Analyzes Rollover Statistics between Near and Next month contracts.
    """

    @staticmethod
    def analyze(symbol: str, near_data: Dict, next_data: Dict) -> Dict[str, Any]:
        """
        Calculates Rollover % and Cost.
        """
        if not near_data or not next_data:
            return {"error": "Missing contract data"}

        near_oi = near_data.get('open_interest', 0)
        next_oi = next_data.get('open_interest', 0)

        total_oi = near_oi + next_oi
        if total_oi == 0:
            rollover_pct = 0.0
        else:
            rollover_pct = (next_oi / total_oi) * 100

        near_price = near_data.get('close', 0)
        next_price = next_data.get('close', 0)

        rollover_cost = next_price - near_price
        rollover_cost_pct = (rollover_cost / near_price * 100) if near_price else 0

        return {
            "symbol": symbol,
            "rollover_pct": round(rollover_pct, 2),
            "rollover_cost": round(rollover_cost, 2),
            "rollover_cost_pct": round(rollover_cost_pct, 2),
            "near_month": {
                "symbol": near_data.get('symbol'),
                "expiry": near_data.get('expiry'),
                "price": near_price,
                "oi": near_oi
            },
            "next_month": {
                "symbol": next_data.get('symbol'),
                "expiry": next_data.get('expiry'),
                "price": next_price,
                "oi": next_oi
            }
        }
