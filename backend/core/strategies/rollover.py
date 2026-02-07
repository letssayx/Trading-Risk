from backend.core.strategies.base import BaseStrategy
import pandas as pd

class RolloverStrategy(BaseStrategy):
    """
    Uses PriceScanner (Spot/Fut) to calculate Basis Yield.
    """
    def run(self, data: pd.DataFrame) -> str:
        # Assumes data has 'future_price', 'spot_price'
        if 'future_price' not in data.columns: return "NO_DATA"

        fut = data['future_price'].iloc[-1]
        spot = data['spot_price'].iloc[-1]
        dte = data['dte'].iloc[-1] if 'dte' in data.columns else 30

        if spot == 0: return "ERROR"

        basis = fut - spot
        yield_pct = (basis / spot) * (365 / dte) * 100

        # Access config if we injected it, or hardcode for MVP core demo
        rfr = 6.0
        if yield_pct > rfr + 1.0:
            return "LONG_BASIS"
        elif yield_pct < rfr - 1.0:
            return "SHORT_BASIS"

        return "NEUTRAL"
