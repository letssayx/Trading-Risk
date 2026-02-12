from typing import Dict, Any, List
import pandas as pd
from sklearn.decomposition import PCA
from backend.domain.toolbox.base import BaseSovereignTool

class MacroStatArbStrategy(BaseSovereignTool):
    """
    Macro StatArb Strategy: PCA-based Factor Analysis.
    """
    @property
    def name(self) -> str: return "Macro StatArb Strategy"
    @property
    def category(self) -> str: return "Strategy"
    @property
    def description(self) -> str: return "Extracts systematic factors using PCA."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {returns_matrix: [[...], [...]]} (List of Lists or DataFrame compatible)
        """
        matrix = data.get("returns_matrix", [])
        if not matrix: return {"error": "No Data"}

        df = pd.DataFrame(matrix)
        # Dropna handled in logic or assumed clean

        pca = PCA(n_components=3) # Default
        pca.fit(df.dropna())

        return {
            "eigenvalues": pca.explained_variance_.tolist(),
            "explained_variance": pca.explained_variance_ratio_.tolist(),
            "components": pca.components_.tolist()
        }

def calculate_pca_factors(returns_matrix: pd.DataFrame, n_components: int = 3) -> Dict[str, Any]:
    # Deprecated wrapper
    strat = MacroStatArbStrategy()
    # Adapt input
    return strat.calculate({"returns_matrix": returns_matrix.values.tolist()})
