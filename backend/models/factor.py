from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import json
import logging
from sklearn.decomposition import PCA
from backend.domain.toolbox.base import BaseSovereignTool

logger = logging.getLogger(__name__)

class FactorExposureModel(BaseSovereignTool):
    """
    Factor Exposure Model using Principal Component Analysis (PCA).

    Decomposes portfolio returns into statistical risk factors (Eigen-Beta).
    Implements a fit/predict interface and supports JSON serialization of model state.
    """
    @property
    def name(self) -> str: return "Factor Exposure Model"

    @property
    def category(self) -> str: return "Risk"

    @property
    def description(self) -> str:
        return "PCA-based Factor Analysis (Eigenvalues/Vectors) for risk decomposition."

    def __init__(self):
        self.pca: Optional[PCA] = None
        self.components_: Optional[List[List[float]]] = None
        self.explained_variance_: Optional[List[float]] = None
        self.mean_: Optional[List[float]] = None
        self.n_components_in_model: int = 0
        self.n_features_in_: int = 0

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper for Sovereign Tool Interface.

        Args:
            data (Dict[str, Any]): Dictionary containing 'returns_matrix' (List[List[float]]).

        Returns:
            Dict[str, Any]: Model card containing eigenvalues and explained variance.
        """
        matrix = data.get("returns_matrix", [])
        if not matrix:
            return {"error": "No Data Provided"}

        try:
            self.fit(matrix)
            return self.model_card
        except Exception as e:
            logger.error(f"Factor Model Calculation Failed: {e}")
            return {"error": str(e)}

    def fit(self, X: List[List[float]], n_components: int = 3) -> None:
        """
        Fits the PCA model to the returns matrix X.

        Args:
            X (List[List[float]]): 2D array of asset returns.
            n_components (int): Number of principal components to keep.
        """
        if not X:
            raise ValueError("Input data X is empty.")

        df = pd.DataFrame(X)
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        # Handle NaNs (simple drop for now, in prod consider imputation)
        df_clean = df.dropna()
        if df_clean.empty:
            raise ValueError("All rows contained NaN and were dropped.")

        # Ensure n_components is valid
        n_samples, n_features = df_clean.shape
        actual_n_components = min(n_components, n_samples, n_features)

        self.pca = PCA(n_components=actual_n_components)
        self.pca.fit(df_clean)

        # Store state
        self.components_ = self.pca.components_.tolist()
        self.explained_variance_ = self.pca.explained_variance_ratio_.tolist()
        self.mean_ = self.pca.mean_.tolist()
        self.n_components_in_model = actual_n_components
        self.n_features_in_ = n_features

        logger.info(f"PCA Fitted with {actual_n_components} components. Variance Explained: {sum(self.explained_variance_):.2%}")

    def predict(self, X: List[List[float]]) -> List[List[float]]:
        """
        Projects new returns onto the learned factors.

        Args:
            X (List[List[float]]): New returns data.

        Returns:
            List[List[float]]: Projected factors (Principal Components).
        """
        if not self.components_ or not self.mean_:
             raise ValueError("Model not fitted. Call fit() first.")

        df = pd.DataFrame(X).fillna(0)
        X_arr = df.values

        # Try using sklearn's transform if available and configured
        if self.pca:
            try:
                return self.pca.transform(X_arr).tolist()
            except Exception as e:
                logger.warning(f"Sklearn transform failed ({e}), falling back to manual projection.")

        # Manual fallback: (X - mean) @ components.T
        # Ensure dimensions match
        if X_arr.shape[1] != len(self.mean_):
             raise ValueError(f"Feature mismatch: Expected {len(self.mean_)}, got {X_arr.shape[1]}")

        X_centered = X_arr - np.array(self.mean_)
        components = np.array(self.components_)
        projected = np.dot(X_centered, components.T)

        return projected.tolist()

    def to_json(self) -> str:
        """
        Serializes the model state to a JSON string.
        """
        if not self.components_:
            return json.dumps({"state": "unfitted"})

        data = {
            "state": "fitted",
            "components": self.components_,
            "mean": self.mean_,
            "explained_variance": self.explained_variance_,
            "n_components": self.n_components_in_model,
            "n_features": self.n_features_in_
        }
        return json.dumps(data)

    def from_json(self, json_str: str) -> None:
        """
        Restores the model state from a JSON string.
        Reconstructs the PCA object manually to allow prediction without re-fitting.
        """
        data = json.loads(json_str)
        if data.get("state") != "fitted":
            logger.warning("Attempted to load unfitted model state.")
            return

        try:
            self.components_ = data["components"]
            self.mean_ = data["mean"]
            self.explained_variance_ = data["explained_variance"]
            self.n_components_in_model = data["n_components"]
            self.n_features_in_ = data.get("n_features", len(self.components_[0]) if self.components_ else 0)

            # Reconstruct sklearn PCA object (best effort)
            self.pca = PCA(n_components=self.n_components_in_model)
            self.pca.components_ = np.array(self.components_)
            self.pca.mean_ = np.array(self.mean_)
            self.pca.explained_variance_ratio_ = np.array(self.explained_variance_)
            self.pca.n_features_in_ = self.n_features_in_

            logger.info("PCA Model successfully restored from JSON.")

        except KeyError as e:
            logger.error(f"Failed to restore model: Missing key {e}")
        except Exception as e:
            logger.error(f"Failed to restore model: {e}")

    @property
    def model_card(self) -> Dict[str, Any]:
        return {
            "model_type": "PCA",
            "parameters": {"n_components": self.n_components_in_model},
            "metrics": {
                "explained_variance_ratio": self.explained_variance_ if self.explained_variance_ else [],
                "total_explained_variance": sum(self.explained_variance_) if self.explained_variance_ else 0.0
            }
        }
