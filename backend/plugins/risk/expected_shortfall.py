import numpy as np

class ExpectedShortfall:
    """
    Conditional Value at Risk (CVaR).
    """
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def calculate(self, portfolio_value: float, returns: list) -> float:
        confidence = self.config.get("confidence_level", 0.99)
        alpha = 1 - confidence

        # Sort returns
        sorted_rets = np.sort(returns)
        # Find cutoff index
        cutoff_index = int(alpha * len(sorted_rets))

        # Average of losses beyond cutoff
        tail_losses = sorted_rets[:cutoff_index]
        if len(tail_losses) == 0:
            return 0.0

        cvar_pct = -np.mean(tail_losses)
        return portfolio_value * cvar_pct
