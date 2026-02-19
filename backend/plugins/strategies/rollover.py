from typing import Dict, Any, List
import pandas as pd
import numpy as np
from backend.domain.toolbox.base import BaseSovereignTool

class RolloverAnalysis(BaseSovereignTool):
    """
    Analyzes Cost of Carry and Rollover Basis for Futures.
    Tracks Near-Next and Next-Far spreads to identify expensive/cheap rollovers.
    """
    @property
    def name(self) -> str: return "Rollover Analysis"
    @property
    def category(self) -> str: return "Strategy" # or Analysis
    @property
    def description(self) -> str: return "Cost of Carry & Basis Z-Score Analysis"

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {
            "near_series": List[float], # Closing prices
            "next_series": List[float],
            "far_series": List[float] (optional),
            "lookback": int (default 24),
            "days_to_expiry": int (default 30)
        }
        """
        near = pd.Series(data.get("near_series", []))
        next_s = pd.Series(data.get("next_series", []))
        far = pd.Series(data.get("far_series", []))
        lookback = data.get("lookback", 24)
        dte = data.get("days_to_expiry", 30)

        if len(near) == 0 or len(next_s) == 0:
            return {"error": "Insufficient Data"}

        # Align lengths
        min_len = min(len(near), len(next_s))
        near = near.iloc[-min_len:]
        next_s = next_s.iloc[-min_len:]

        # 1. Near-Next Analysis
        basis_nn = next_s - near
        ann_basis_nn = (basis_nn / near) * (365 / dte) * 100

        current_basis_nn = basis_nn.iloc[-1]
        current_ann_nn = ann_basis_nn.iloc[-1]

        # Z-Score (Historical)
        if len(ann_basis_nn) > 1:
            rolling_mean = ann_basis_nn.rolling(lookback).mean()
            rolling_std = ann_basis_nn.rolling(lookback).std()
            z_score_nn = (current_ann_nn - rolling_mean.iloc[-1]) / (rolling_std.iloc[-1] + 1e-9)
        else:
            z_score_nn = 0.0

        result = {
            "near_next": {
                "basis": float(current_basis_nn),
                "annualized_pct": float(current_ann_nn),
                "z_score": float(z_score_nn)
            }
        }

        # 2. Next-Far Analysis
        if len(far) > 0:
            min_len_f = min(len(next_s), len(far))
            next_s_f = next_s.iloc[-min_len_f:]
            far_f = far.iloc[-min_len_f:]

            basis_nf = far_f - next_s_f
            ann_basis_nf = (basis_nf / next_s_f) * (365 / dte) * 100

            current_basis_nf = basis_nf.iloc[-1]
            current_ann_nf = ann_basis_nf.iloc[-1]

            if len(ann_basis_nf) > 1:
                rolling_mean_f = ann_basis_nf.rolling(lookback).mean()
                rolling_std_f = ann_basis_nf.rolling(lookback).std()
                z_score_nf = (current_ann_nf - rolling_mean_f.iloc[-1]) / (rolling_std_f.iloc[-1] + 1e-9)
            else:
                z_score_nf = 0.0

            result["next_far"] = {
                "basis": float(current_basis_nf),
                "annualized_pct": float(current_ann_nf),
                "z_score": float(z_score_nf)
            }

        return result
