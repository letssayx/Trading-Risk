import numpy as np
import pandas as pd
from backend.core.stats.regression import RegressionSuite

class APTModel:
    """
    Arbitrage Pricing Theory (APT) Multi-Factor Model.
    $R_i = \alpha + \beta_1 F_1 + \beta_2 F_2 + ... + \beta_n F_n + \epsilon$

    Factors (F) can be Macro Indicators (DXY, Oil, Yields).
    """
    def __init__(self):
        self.regression = RegressionSuite()

    def calculate_betas(self, asset_returns: pd.Series, factor_matrix: pd.DataFrame) -> dict:
        """
        Input:
          asset_returns: Series of asset % returns.
          factor_matrix: DataFrame of Factor % returns (Cols: DXY, OIL, VIX, etc.)
        Output:
          Dictionary of Factor Betas.
        """
        # Align data
        combined = pd.concat([asset_returns, factor_matrix], axis=1).dropna()
        if len(combined) < 30: return {"error": "Insufficient Data"}

        y = combined.iloc[:, 0].values
        X = combined.iloc[:, 1:].values
        factors = combined.columns[1:]

        # Multi-Variate Regression (Using numpy linalg for efficiency as RegressionSuite is univariate OLS)
        # Adding intercept col
        X_design = np.column_stack([np.ones(len(X)), X])

        try:
            # Beta = (X'X)^-1 X'y
            beta_coeffs = np.linalg.lstsq(X_design, y, rcond=None)[0]

            result = {"alpha": beta_coeffs[0]}
            for idx, factor in enumerate(factors):
                result[factor] = beta_coeffs[idx + 1]

            return result
        except Exception as e:
            return {"error": str(e)}
