from typing import Any, Dict
from backend.strategies.turtle import TurtleLegacyStrategy
from backend.strategies.vol_arb import calculate_vol_spread
from backend.domain.portfolio.manager import PortfolioManager # Mock dependency for instantiation

class StrategyLibrary:
    """
    Registry of OOTB Strategies available for instantiation.
    """

    @staticmethod
    def get_turtle_strategy(capital: float = 1000000.0) -> TurtleLegacyStrategy:
        # Create a dummy manager for the strategy object
        pm = PortfolioManager([], total_capital=capital)
        return TurtleLegacyStrategy(portfolio_manager=pm)

    @staticmethod
    def run_vol_arb_check(iv_near: float, iv_far: float) -> Dict[str, Any]:
        return calculate_vol_spread(iv_near, iv_far)

# Expose instances? Usually classes or factories.
# Toolbox logic suggests "Tools".
