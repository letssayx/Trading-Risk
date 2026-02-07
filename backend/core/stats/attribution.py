import pandas as pd
from backend.core.stats.factor import APTModel

class PerformanceAttribution:
    """
    Analyzes Trade Performance and Attributes PnL to Factors.
    """
    def __init__(self):
        self.apt = APTModel()

    def calculate_metrics(self, trade_record: dict) -> dict:
        """
        Input: dict with entry_price, exit_price, entry_time, exit_time
        """
        entry = trade_record.get('entry_price', 0)
        exit_p = trade_record.get('exit_price', 0)

        if entry == 0: return {}

        roi = (exit_p - entry) / entry

        # Duration in Days (Mock)
        # In real app: (exit_time - entry_time).days
        duration = 5

        return {
            "roi_pct": roi * 100,
            "holding_period_days": duration,
            "pnl": (exit_p - entry) * trade_record.get('quantity', 1)
        }

    def attribute_factors(self, trade_returns: pd.Series, macro_factors: pd.DataFrame) -> dict:
        """
        Uses APT to explain WHICH factor drove the return.
        """
        betas = self.apt.calculate_betas(trade_returns, macro_factors)

        # Attribution: Factor Return * Beta
        attribution = {}
        for factor in macro_factors.columns:
            factor_return = macro_factors[factor].mean() # Average factor move during trade
            beta = betas.get(factor, 0)
            attribution[factor] = factor_return * beta

        # Specific Return (Alpha) is the residual
        return attribution
