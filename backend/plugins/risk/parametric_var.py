import numpy as np
from scipy.stats import norm

class ParametricVaR:
    """
    Standard Variance-Covariance VaR Model.
    """
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def calculate(self, portfolio_value: float, returns: list) -> float:
        confidence = self.config.get("confidence_level", 0.99)
        horizon = self.config.get("horizon_days", 1)

        vol = np.std(returns)
        z_score = norm.ppf(confidence)

        return portfolio_value * vol * z_score * np.sqrt(horizon)
