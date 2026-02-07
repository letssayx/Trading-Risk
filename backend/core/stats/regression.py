import numpy as np
from scipy import stats

class RegressionSuite:
    """
    OLS Regression Model.
    y = beta * X + alpha
    """
    def run_ols(self, x: list, y: list):
        if len(x) != len(y) or len(x) < 2:
            return {"beta": 0, "alpha": 0, "r_sq": 0}

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return {
            "beta": slope,
            "alpha": intercept,
            "r_sq": r_value**2,
            "p_value": p_value
        }
