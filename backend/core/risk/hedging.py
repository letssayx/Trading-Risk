import numpy as np

class SystematicHedge:
    """
    Beta-Weighted Hedging.
    """
    def calculate_hedge_ratio(self, portfolio_beta: float, portfolio_value: float, index_value: float) -> int:
        """
        Returns number of Index Futures to short.
        """
        exposure = portfolio_value * portfolio_beta
        contracts = exposure / index_value
        return int(round(contracts))

class ConvexityEngine:
    """
    Vomma Calculation.
    """
    def calculate_vomma(self, vega: float, vol: float) -> float:
        # Simplistic proxy: Vomma ~ Vega / Vol (Sensitivity of Vega to Vol)
        if vol == 0: return 0.0
        return vega / vol
