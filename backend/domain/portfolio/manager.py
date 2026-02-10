from typing import List, Dict, Optional
from backend.domain.portfolio.models import Trade, TradeSide

class PortfolioManager:
    def __init__(self, trades: List[Trade], total_capital: float = 1000000.0):
        self.trades = trades
        self.total_capital = total_capital

    def get_total_capital(self) -> float:
        return self.total_capital

    def update_capital(self, new_capital: float):
        self.total_capital = new_capital

    def calculate_total_greeks(self) -> Dict[str, float]:
        """
        Aggregates Greeks from all open trades.
        Assumes 'greeks' dictionary is present in trade.meta_data or calculated elsewhere.
        """
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0

        for trade in self.trades:
            if trade.status == "OPEN":
                # In a real system, this would call a pricing model with current market data.
                # Here we assume the latest greeks are stored/cached in meta_data.
                greeks = trade.meta_data.get("greeks", {})
                qty = trade.qty
                direction = 1 if trade.side == TradeSide.BUY else -1

                total_delta += greeks.get("delta", 0.0) * qty * direction
                total_gamma += greeks.get("gamma", 0.0) * qty * direction # Gamma is usually positive for long options
                total_vega += greeks.get("vega", 0.0) * qty # Vega is positive for long options
                total_theta += greeks.get("theta", 0.0) * qty # Theta is negative for long options

        return {
            "delta": total_delta,
            "gamma": total_gamma,
            "vega": total_vega,
            "theta": total_theta
        }

    def get_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Calculates unrealized PnL based on current market prices.
        """
        pnl = 0.0
        for trade in self.trades:
            if trade.status == "OPEN":
                current_price = current_prices.get(trade.ticker)
                if current_price is None:
                    continue # Skip if no price available

                entry_price = trade.price
                direction = 1 if trade.side == TradeSide.BUY else -1

                # Simple linear PnL (futures/stocks). Options would need Black-Scholes.
                # Assuming this is linear for now or the 'current_price' is the option premium.
                pnl += (current_price - entry_price) * trade.qty * direction
        return pnl

    def get_exposure_by_sector(self, sector_map: Dict[str, str]) -> Dict[str, float]:
        exposure = {}
        for trade in self.trades:
            if trade.status == "OPEN":
                sector = sector_map.get(trade.ticker, "Unknown")
                amount = trade.qty * trade.price # Notional exposure
                exposure[sector] = exposure.get(sector, 0.0) + amount
        return exposure
