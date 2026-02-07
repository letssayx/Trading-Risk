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
        vol_model = self.config.get("vol_model", "HISTORICAL") # HISTORICAL or GARCH_PROXY

        alpha = 1 - confidence

        # Simulate GARCH effect: Scale recent returns if volatility clustering detected
        # (Proxy logic until 'arch' package is available)
        final_returns = np.array(returns)
        if vol_model == "GARCH_PROXY":
            recent_vol = np.std(final_returns[-20:]) if len(final_returns) > 20 else np.std(final_returns)
            long_term_vol = np.std(final_returns)
            if long_term_vol > 0:
                scaling_factor = recent_vol / long_term_vol
                final_returns = final_returns * scaling_factor

        # Sort returns
        sorted_rets = np.sort(final_returns)
        # Find cutoff index
        cutoff_index = int(alpha * len(sorted_rets))

        # Average of losses beyond cutoff
        tail_losses = sorted_rets[:cutoff_index]
        if len(tail_losses) == 0:
            return 0.0

        cvar_pct = -np.mean(tail_losses)
        return portfolio_value * cvar_pct
