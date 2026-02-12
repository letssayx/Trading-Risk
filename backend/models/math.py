import numpy as np
from typing import Dict, Any, List
from backend.domain.toolbox.base import BaseSovereignTool

class CompoundingAuditor(BaseSovereignTool):
    """
    Adjusts returns for geometric compounding.
    """
    @property
    def name(self) -> str: return "Compounding Auditor"
    @property
    def category(self) -> str: return "Math"
    @property
    def description(self) -> str: return "Calculates Geometric Mean Return vs Arithmetic Mean."

    def calculate(self, data: List[float]) -> Dict[str, Any]:
        """
        data: List of returns (e.g. 0.01, -0.02)
        """
        returns = np.array(data)
        arithmetic = np.mean(returns)
        # Geometric Mean: (Product(1+r))^(1/n) - 1
        geometric = (np.prod(1 + returns))**(1/len(returns)) - 1

        drag = arithmetic - geometric

        return {
            "arithmetic_mean": arithmetic,
            "geometric_mean": geometric,
            "volatility_drag": drag
        }
