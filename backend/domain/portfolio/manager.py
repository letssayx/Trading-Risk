from typing import List, Dict, Any
from backend.domain.portfolio.models import Trade, TradeSide, Portfolio
from backend.risk.greeks import calculate_total_greeks

class PortfolioManager:
    """
    Manages Portfolio State (Capital, Trades).
    Delegates calculations to Risk Engine.
    """
    def __init__(self, trades: List[Trade], total_capital: float = 1000000.0):
        self.trades = trades
        self.total_capital = total_capital

    def get_total_capital(self) -> float:
        return self.total_capital

    def update_capital(self, new_capital: float):
        self.total_capital = new_capital

    def get_portfolio_greeks(self) -> Dict[str, float]:
        """
        Delegates to the refactored risk.greeks module.
        """
        return calculate_total_greeks(self.trades)

    def get_portfolio_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Calculates unrealized PnL based on current market prices.
        Moved logic inline or to a new PnL module (kept inline for simplicity here as it wasn't the main refactor target).
        """
        pnl = 0.0
        for trade in self.trades:
            if trade.status == "OPEN":
                current_price = current_prices.get(trade.ticker)
                if current_price is None:
                    continue

                entry_price = trade.price
                # Direction: 1 for Buy, -1 for Sell
                direction = 1 if trade.side == TradeSide.BUY else -1
                pnl += (current_price - entry_price) * float(trade.qty) * direction
        return pnl

    def get_exposure_by_sector(self, sector_map: Dict[str, str]) -> Dict[str, float]:
        exposure = {}
        for trade in self.trades:
            if trade.status == "OPEN":
                sector = sector_map.get(trade.ticker, "Unknown")
                amount = float(trade.qty) * trade.price
                exposure[sector] = exposure.get(sector, 0.0) + amount
        return exposure

    def calculate_nav_breakdown(self, sub_portfolios: List[Portfolio], current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates Net Asset Value (NAV) for the Master Fund and breakdowns for sub-portfolios.
        """
        master_pnl = self.get_portfolio_pnl(current_prices)
        master_nav = self.total_capital + master_pnl

        breakdown = []
        for p in sub_portfolios:
            # Filter trades for this portfolio
            p_trades = [t for t in self.trades if t.portfolio_id == p.id]

            # Re-implement PnL logic locally for sub-portfolio slice
            sub_pnl = 0.0
            pos_value = 0.0
            for t in p_trades:
                if t.status == "OPEN":
                    cp = current_prices.get(t.ticker, t.price)
                    dr = 1 if t.side == TradeSide.BUY else -1
                    sub_pnl += (cp - t.price) * float(t.qty) * dr
                    pos_value += float(t.qty) * cp

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
