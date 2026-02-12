from typing import List, Dict, Any
from backend.domain.portfolio.models import Trade, TradeSide

class RiskCalculations:
    """
    Pure calculation engine for Portfolio Risk.
    """
    @staticmethod
    def calculate_total_greeks(trades: List[Trade]) -> Dict[str, float]:
        """
        Aggregates Greeks from all open trades.
        """
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0

        for trade in trades:
            if trade.status == "OPEN":
                greeks = trade.meta_data.get("greeks", {})
                qty = trade.qty
                direction = 1 if trade.side == TradeSide.BUY else -1

                total_delta += greeks.get("delta", 0.0) * qty * direction
                total_gamma += greeks.get("gamma", 0.0) * qty * direction
                total_vega += greeks.get("vega", 0.0) * qty
                total_theta += greeks.get("theta", 0.0) * qty

        return {
            "delta": total_delta,
            "gamma": total_gamma,
            "vega": total_vega,
            "theta": total_theta
        }

    @staticmethod
    def calculate_unrealized_pnl(trades: List[Trade], current_prices: Dict[str, float]) -> float:
        """
        Calculates unrealized PnL based on current market prices.
        """
        pnl = 0.0
        for trade in trades:
            if trade.status == "OPEN":
                current_price = current_prices.get(trade.ticker)
                if current_price is None:
                    continue

                entry_price = trade.price
                direction = 1 if trade.side == TradeSide.BUY else -1
                pnl += (current_price - entry_price) * trade.qty * direction
        return pnl
