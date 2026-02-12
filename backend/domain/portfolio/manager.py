from typing import List, Dict, Optional, Any
from backend.domain.portfolio.models import Trade, TradeSide, Portfolio
from backend.risk.calculations import RiskCalculations

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
        return RiskCalculations.calculate_total_greeks(self.trades)

    def get_portfolio_pnl(self, current_prices: Dict[str, float]) -> float:
        return RiskCalculations.calculate_unrealized_pnl(self.trades, current_prices)

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
        """
        master_pnl = self.get_portfolio_pnl(current_prices)
        master_nav = self.total_capital + master_pnl

        breakdown = []
        for p in sub_portfolios:
            # Filter trades for this portfolio
            p_trades = [t for t in self.trades if t.portfolio_id == p.id]

            sub_pnl = RiskCalculations.calculate_unrealized_pnl(p_trades, current_prices)

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
