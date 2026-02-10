from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

def calculate_pca_factors(
    returns_matrix: pd.DataFrame,
    n_components: int = 3
) -> Dict[str, Any]:
    """
    Performs Principal Component Analysis (PCA) on asset returns to isolate systematic factors.

    Args:
        returns_matrix: DataFrame (Time x Assets).
        n_components: Number of factors to extract (usually 3-5).

    Returns:
        Dict with Eigenvalues, Explained Variance, and Factor Loadings.
    """
    pca = PCA(n_components=n_components)
    pca.fit(returns_matrix.dropna())

    explained_variance = pca.explained_variance_ratio_
    eigenvalues = pca.explained_variance_
    loadings = pca.components_

    factors = pca.transform(returns_matrix.dropna())

    # Isolate "Alpha" (Residuals)
    # Reconstruct returns using components
    reconstructed = pca.inverse_transform(factors)
    residuals = returns_matrix.dropna() - reconstructed

    return {
        "eigenvalues": eigenvalues.tolist(),
        "explained_variance": explained_variance.tolist(),
        "factor_loadings": loadings.tolist(),
        "residuals": residuals,
        "factors": factors
    }
