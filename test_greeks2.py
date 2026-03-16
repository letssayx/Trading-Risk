import numpy as np
import warnings

warnings.simplefilter('always', RuntimeWarning)

def calculate_implied_volatility(
    target_price: float, S: float, K: float, T: float, r: float, option_type: str = "call"
) -> float:
    MAX_ITER = 100
    TOLERANCE = 1e-5
    sigma = 0.3

    for i in range(MAX_ITER):
        # We dummy this to force sigma to get huge
        diff = target_price - 1.0
        vega = 0.000000001

        # In actual code: sigma = sigma + diff / vega
        sigma = sigma + diff / vega

        print("sigma:", sigma)
        if i > 5: break

calculate_implied_volatility(100, 100, 100, 0.5, 0.05)
