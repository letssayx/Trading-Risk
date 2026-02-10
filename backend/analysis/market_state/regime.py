import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from hmmlearn.hmm import GaussianHMM

class RegimeDetector:
    """
    Detects market regimes using Hidden Markov Models (HMM).
    States:
    - 0: Quiet Bull (Low Vol, Pos Ret)
    - 1: Sideways (Med Vol, Flat Ret)
    - 2: High-Vol Bear (High Vol, Neg Ret)
    """

    def __init__(self, n_components: int = 3, covariance_type: str = "full"):
        self.model = GaussianHMM(
            n_components=n_components,
            covariance_type=covariance_type,
            n_iter=100,
            random_state=42
        )
        self.states_map = {0: "Unknown", 1: "Unknown", 2: "Unknown"}

    def detect_market_regime(
        self,
        returns: pd.Series,
        volatility: pd.Series,
        volume: pd.Series
    ) -> Dict[str, Any]:
        """
        Fits HMM and predicts the current market state.

        Args:
            returns: Daily log returns.
            volatility: Daily volatility (e.g. ATR or GARCH).
            volume: Daily volume (standardized).

        Returns:
            Dict containing current state, probabilities, and transition matrix.
        """
        # Align data
        df = pd.DataFrame({
            "returns": returns,
            "volatility": volatility,
            "volume": volume
        }).dropna()

        if len(df) < 50:
            return {"state": "Insufficient Data", "probs": []}

        # Prepare features (Returns, Volatility, Volume)
        X = df.values

        # Fit Model
        try:
            self.model.fit(X)
            hidden_states = self.model.predict(X)
            current_state = hidden_states[-1]
            probs = self.model.predict_proba(X)[-1]
        except ValueError:
            return {"state": "Fit Error", "probs": []}

        # Identify States (Post-hoc Labeling)
        # Calculate mean Returns/Vol for each component to label them
        means = self.model.means_
        # means shape: (n_components, n_features)
        # feature 0: returns, 1: volatility

        # Sort states by Volatility (Low -> High)
        sorted_indices = np.argsort(means[:, 1])

        # Heuristic labeling based on sorted Volatility
        # Lowest Vol -> Quiet Bull? (Check returns)
        # Highest Vol -> Bear? (Check returns < 0)

        state_labels = {}

        # Assume 0=Low Vol, 1=Med Vol, 2=High Vol
        if len(sorted_indices) > 0:
            state_labels[sorted_indices[0]] = "Quiet Bull"
        if len(sorted_indices) > 1:
            state_labels[sorted_indices[1]] = "Sideways / Choppy"
        if len(sorted_indices) > 2:
            state_labels[sorted_indices[2]] = "High-Vol Bear"

        # Refine labels based on Returns if needed
        # e.g. if High Vol has positive returns -> High Vol Rally

        detected_label = state_labels.get(current_state, "Unknown")

        return {
            "current_state_id": int(current_state),
            "current_state_label": detected_label,
            "state_probs": {state_labels[i]: p for i, p in enumerate(probs)},
            "means": means.tolist(),
            "transition_matrix": self.model.transmat_.tolist()
        }
