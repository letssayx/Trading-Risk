import pandas as pd
import logging
from typing import Dict, Any, List, Tuple
from backend.domain.toolbox.base import BaseSovereignTool

logger = logging.getLogger(__name__)

class StatArbAlphaEngine(BaseSovereignTool):
    """
    Statistical Arbitrage Alpha Engine.

    Detects Mean Reversion and Z-Score Divergence using statistical arbitrage logic.
    Calculates the spread between two asset series, computes the Z-Score, and generates
    trading signals based on predefined thresholds.
    """
    @property
    def name(self) -> str: return "StatArb Alpha Engine"

    @property
    def category(self) -> str: return "Strategy"

    @property
    def description(self) -> str:
        return "Identifies Z-Score divergence for Pairs Trading using mean reversion."

    def calculate(self, data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Executes the Alpha Engine logic.

        Args:
            data (Dict[str, List[float]]): Dictionary containing input time series:
                - 'series_a': List of prices for asset A.
                - 'series_b': List of prices for asset B.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - z_score (float): The current Z-Score of the spread.
                - mean_spread (float): The mean of the spread.
                - std_spread (float): The standard deviation of the spread.
                - signal (str): The trading signal ("LONG_SPREAD", "SHORT_SPREAD", "NEUTRAL").
                - error (str, optional): Error message if calculation fails.
        """
        try:
            series_a, series_b = self._validate_input(data)
            spread = self._compute_spread(series_a, series_b)
            stats = self._compute_stats(spread)
            signal = self._derive_signal(stats["z_score"])

            logger.info(f"Alpha Engine Calculated: Z-Score={stats['z_score']:.2f}, Signal={signal}")

            return {
                "z_score": stats["z_score"],
                "mean_spread": stats["mean"],
                "std_spread": stats["std"],
                "signal": signal
            }
        except ValueError as e:
            logger.warning(f"Validation Error in Alpha Engine: {e}")
            return {"error": str(e)}
        except Exception:
            logger.exception("Unexpected Error in Alpha Engine")
            return {"error": "Internal Calculation Error"}

    def _validate_input(self, data: Dict[str, List[float]]) -> Tuple[pd.Series, pd.Series]:
        """
        Validates and converts input data to Pandas Series.

        Raises:
            ValueError: If input data is missing, empty, or mismatched in length.
        """
        series_a_list = data.get("series_a", [])
        series_b_list = data.get("series_b", [])

        if not series_a_list or not series_b_list:
            raise ValueError("Input series cannot be empty")

        sa = pd.Series(series_a_list, dtype=float)
        sb = pd.Series(series_b_list, dtype=float)

        if len(sa) != len(sb):
            raise ValueError(f"Series length mismatch: A={len(sa)}, B={len(sb)}")

        return sa, sb

    def _compute_spread(self, a: pd.Series, b: pd.Series) -> pd.Series:
        """
        Computes the spread between two series (A - B).
        In a production environment, this should use a Hedge Ratio (OLS).
        """
        return a - b

    def _compute_stats(self, spread: pd.Series) -> Dict[str, float]:
        """
        Computes statistical metrics (Mean, Std, Z-Score) for the spread.
        """
        mean = spread.mean()
        std = spread.std()

        if pd.isna(std) or std == 0:
            logger.warning("Spread standard deviation is 0 or NaN. Z-Score defaulted to 0.")
            z_score = 0.0
        else:
            current_val = spread.iloc[-1]
            z_score = (current_val - mean) / std

        return {
            "mean": float(mean) if not pd.isna(mean) else 0.0,
            "std": float(std) if not pd.isna(std) else 0.0,
            "z_score": float(z_score)
        }

    def _derive_signal(self, z_score: float) -> str:
        """
        Generates a trading signal based on Z-Score thresholds.

        - Z > 2.0: SHORT_SPREAD (Spread is too high, expect reversion)
        - Z < -2.0: LONG_SPREAD (Spread is too low, expect reversion)
        - Otherwise: NEUTRAL
        """
        if z_score > 2.0:
            return "SHORT_SPREAD"
        elif z_score < -2.0:
            return "LONG_SPREAD"
        return "NEUTRAL"
