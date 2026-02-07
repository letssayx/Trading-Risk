import numpy as np
import pandas as pd

class PCANalyzer:
    """
    Principal Component Analysis (PCA) for Dimensionality Reduction.
    Used to extract 'Primary Drivers' (Eigenvectors) of a sector.
    """
    def fit(self, returns_matrix: pd.DataFrame, n_components: int = 3) -> dict:
        """
        Input: DataFrame of returns (Cols = Stocks, Rows = Time)
        Output: Explained Variance Ratio, Principal Components.
        """
        # Standardize
        data = returns_matrix.dropna()
        if len(data) < 20: return {"error": "Insufficient Data"}

        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        standardized = (data - mean) / std

        # Covariance Matrix
        cov_matrix = np.cov(standardized.T)

        # Eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        # Sort desc
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Explained Variance
        total_var = sum(eigenvalues)
        explained_variance_ratio = eigenvalues / total_var

        return {
            "explained_variance": explained_variance_ratio[:n_components].tolist(),
            "components": eigenvectors[:, :n_components].tolist(), # Loadings
            "features": list(returns_matrix.columns)
        }
