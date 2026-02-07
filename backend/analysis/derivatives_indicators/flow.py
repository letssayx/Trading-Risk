from typing import Literal

def get_oi_quadrant(price_change_pct: float, oi_change_pct: float) -> str:
    """
    Classifies Market Action into 4 Quadrants:
    1. Long Buildup: Price UP, OI UP
    2. Short Buildup: Price DOWN, OI UP
    3. Short Covering: Price UP, OI DOWN
    4. Long Unwinding: Price DOWN, OI DOWN
    """
    if price_change_pct > 0:
        if oi_change_pct > 0:
            return "LONG_BUILDUP"
        else:
            return "SHORT_COVERING"
    else:
        if oi_change_pct > 0:
            return "SHORT_BUILDUP"
        else:
            return "LONG_UNWINDING"
