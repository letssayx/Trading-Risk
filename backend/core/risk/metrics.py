import numpy as np
from scipy.stats import norm

class ParametricVaR:
    """
    Standard Variance-Covariance VaR.
    """
    def calculate(self, portfolio_value: float, vol: float, confidence: float = 0.99) -> float:
        z_score = norm.ppf(confidence)
        return portfolio_value * vol * z_score

class ExpectedShortfall:
    """
    Conditional Value at Risk (CVaR).
    Mean of losses exceeding VaR.
    """
    def calculate(self, portfolio_value: float, returns: list, confidence: float = 0.99) -> float:
        alpha = 1 - confidence
        sorted_rets = np.sort(returns)
        cutoff_index = int(alpha * len(sorted_rets))

        tail_losses = sorted_rets[:cutoff_index]
        if len(tail_losses) == 0: return 0.0

        cvar_pct = -np.mean(tail_losses)
        return portfolio_value * cvar_pct
