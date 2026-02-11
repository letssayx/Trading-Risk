from typing import List, Dict, Optional, Any
from backend.domain.portfolio.models import Trade, TradeSide, Portfolio

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
        """
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0

        for trade in self.trades:
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

    def get_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Calculates unrealized PnL based on current market prices.
        """
        pnl = 0.0
        for trade in self.trades:
            if trade.status == "OPEN":
                current_price = current_prices.get(trade.ticker)
                if current_price is None:
                    continue

                entry_price = trade.price
                direction = 1 if trade.side == TradeSide.BUY else -1
                pnl += (current_price - entry_price) * trade.qty * direction
        return pnl

    def get_exposure_by_sector(self, sector_map: Dict[str, str]) -> Dict[str, float]:
        exposure = {}
        for trade in self.trades:
            if trade.status == "OPEN":
                sector = sector_map.get(trade.ticker, "Unknown")
                amount = trade.qty * trade.price
                exposure[sector] = exposure.get(sector, 0.0) + amount
        return exposure

    def calculate_nav_breakdown(self, sub_portfolios: List[Portfolio], current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates Net Asset Value (NAV) for the Master Fund and breakdowns for sub-portfolios.
        NAV = Cash + Market Value of Positions.
        Currently approximating based on PnL + Capital.
        """
        master_nav = self.total_capital + self.get_unrealized_pnl(current_prices)

        breakdown = []
        for p in sub_portfolios:
            # Filter trades for this portfolio
            p_trades = [t for t in self.trades if t.portfolio_id == p.id]
            # Use a temp manager
            sub_mgr = PortfolioManager(p_trades)
            sub_pnl = sub_mgr.get_unrealized_pnl(current_prices)
            # Assuming capital allocated per portfolio? Or just PnL attribution.
            # Let's return PnL and Position Value.
            pos_value = sum([t.qty * current_prices.get(t.ticker, t.price) for t in p_trades if t.status == "OPEN"])

            breakdown.append({
                "portfolio_id": str(p.id),
                "name": p.name,
                "unrealized_pnl": sub_pnl,
                "gross_position_value": pos_value
            })

        return {
            "master_nav": master_nav,
            "sub_portfolios": breakdown
        }
