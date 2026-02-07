import numpy as np

class VolatilityForecaster:
    """
    GARCH(1,1) Proxy using Exponential Decay.
    sigma_sq_t = omega + alpha * eps_sq + beta * sigma_sq_prev
    """
    def predict(self, returns: list) -> float:
        if len(returns) < 2: return 0.0

        # Proxy: EWMA Volatility
        # This approximates GARCH behavior where recent shocks have higher weight
        series = np.array(returns)
        alpha = 0.94 # Decay factor (RiskMetrics standard)

        # Simple EWMA loop (optimized)
        var = np.var(series) # Initial estimate
        for r in series:
            var = alpha * var + (1 - alpha) * (r**2)

        return np.sqrt(var)
