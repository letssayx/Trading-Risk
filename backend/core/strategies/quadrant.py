from backend.core.strategies.base import BaseStrategy
import pandas as pd

class QuadrantStrategy(BaseStrategy):
    """
    Uses PriceScanner and OIScanner to detect Long Buildup vs Short Covering.
    """
    def run(self, data: pd.DataFrame) -> str:
        price_chg = self.indicators['price'].compute(data)
        oi_chg = self.indicators['oi'].compute(data)

        if price_chg > 0 and oi_chg > 0:
            return "LONG_BUILDUP"
        elif price_chg > 0 and oi_chg < 0:
            return "SHORT_COVERING"
        elif price_chg < 0 and oi_chg > 0:
            return "SHORT_BUILDUP"
        else:
            return "LONG_UNWINDING"
