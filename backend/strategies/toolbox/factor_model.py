from typing import Dict, Any, List
import pandas as pd
from backend.domain.toolbox.base import BaseSovereignTool
from backend.strategies.macro_stat_arb import calculate_pca_factors

class FactorExposureModel(BaseSovereignTool):
    """
    Decomposes portfolio returns into PCA Factors (Eigen-Beta).
    """
    @property
    def name(self) -> str: return "Factor Exposure Model"
    @property
    def category(self) -> str: return "Risk"
    @property
    def description(self) -> str: return "PCA-based Factor Analysis (Eigenvalues/Vectors)."

    def calculate(self, data: Dict[str, List[List[float]]]) -> Dict[str, Any]:
        """
        data: {"returns_matrix": [[...], [...]]}
        """
        matrix = data.get("returns_matrix", [])
        if not matrix: return {"error": "No Data"}

        df = pd.DataFrame(matrix)
        res = calculate_pca_factors(df, n_components=3)

        return {
            "eigenvalues": res["eigenvalues"],
            "explained_variance": res["explained_variance"]
        }
