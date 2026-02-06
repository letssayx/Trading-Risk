from typing import Dict, Any

class SkewPercentile:
    """
    Compares 25D Put IV vs 25D Call IV.
    """
    def calculate_skew(self, put_iv: float, call_iv: float) -> float:
        return put_iv - call_iv
