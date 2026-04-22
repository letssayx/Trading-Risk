import numpy as np
import pandas as pd
from typing import Dict, Optional
from backend.risk.measures.optimization import calculate_risk_contributions

class RiskManager:
    def __init__(self):
        pass

    def check_risk_imbalance(
        self,
        weights: pd.Series,
        cov_matrix: pd.DataFrame,
        risk_budgets: Optional[pd.Series] = None,
        threshold: float = 0.15
    ) -> Dict[str, Dict[str, float]]:
        """
        Checks for Risk Imbalance using Euler decomposition.
        Flags assets where Risk Contribution > Risk Budget * (1 + threshold).
        """
        # Calculate Risk Contributions
        # RC is dollar risk contribution. To compare with budget (percentage), we need % RC.
        # calculate_risk_contributions returns fractional contribution (sum=1).

        rc_pct = calculate_risk_contributions(weights, cov_matrix)

        if risk_budgets is None:
            # Default to Equal Risk Contribution
            n = len(weights)
            risk_budgets = pd.Series([1.0/n]*n, index=weights.index)

        imbalances = {}

        for asset in weights.index:
            contrib = rc_pct.get(asset, 0.0)
            budget = risk_budgets.get(asset, 0.0)

            # Check if contribution exceeds budget by threshold
            # E.g., Budget 20%, Threshold 15% -> Limit 23%? Or 20% + 15% = 35%?
            # Prompt says: "exceeds its assigned 'Risk Budget' by > 15%."
            # Usually means relative: (Contrib - Budget) / Budget > 0.15?
            # Or absolute: Contrib > Budget + 0.15?
            # Given weights are small (e.g. 0.05), absolute 0.15 is huge.
            # I'll assume relative deviation: Contrib > Budget * (1 + threshold).

            if budget > 0:
                deviation = (contrib - budget) / budget
            else:
                deviation = float('inf') if contrib > 0 else 0.0

            if deviation > threshold:
                imbalances[asset] = {
                    "contribution": contrib,
                    "budget": budget,
                    "deviation": deviation,
                    "status": "IMBALANCED"
                }

        return imbalances

    def suggest_risk_balanced_weights(
        self,
        cov_matrix: pd.DataFrame,
        risk_budgets: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Calculates suggested weights to align Risk Contributions with Risk Budgets.
        Uses a simple iterative approach (Risk Parity / ERC algorithm).
        """
        n_assets = cov_matrix.shape[0]
        assets = cov_matrix.index

        if risk_budgets is None:
            risk_budgets = pd.Series([1.0/n_assets]*n_assets, index=assets)

        # Initial weights: Inverse Volatility or Equal Weight
        # Let's start with Equal Weights
        weights = pd.Series([1.0/n_assets]*n_assets, index=assets)

        # Simple iterative scaling: w_new = w_old * (budget / contribution)
        # Iterate 50 times or until convergence
        for _ in range(50):
            rc = calculate_risk_contributions(weights, cov_matrix)

            # Avoid division by zero
            rc = rc.replace(0, 1e-9)

            # Update weights
            # w_new_i = w_i * (b_i / RC_i)
            # Normalize weights to sum to 1?
            # Standard Risk Parity usually targets weights summing to 1 (fully invested)
            # or uses leverage. Here we assume fully invested long-only for simplicity.

            # Damped update for stability: w_new = w * (b / rc)^0.5
            ratio = risk_budgets / rc
            new_weights = weights * np.power(ratio, 0.5)

            # Normalize to sum to 1
            if new_weights.sum() > 0:
                new_weights /= new_weights.sum()
            else:
                new_weights = pd.Series([1.0/n_assets]*n_assets, index=assets)

            # Check convergence
            if np.allclose(weights, new_weights, atol=1e-4):
                break

            weights = new_weights

        return weights
