import numpy as np
from typing import Dict, Any, List
from backend.domain.toolbox.base import BaseSovereignTool
from backend.risk.tests import calculate_lr_cc

class GovernanceAuditor(BaseSovereignTool):
    """
    Audits Model Performance (LRcc, Kupiec).
    """
    @property
    def name(self) -> str: return "Governance Auditor"
    @property
    def category(self) -> str: return "Governance"
    @property
    def description(self) -> str: return "Validates Risk Models using Statistical Tests (LRcc)."

    def calculate(self, data: List[int]) -> Dict[str, Any]:
        """
        data: List of binary breaches (0, 1)
        """
        breaches = np.array(data)
        lr_cc, p_val, decision, details = calculate_lr_cc(breaches)

        return {
            "decision": decision,
            "score": lr_cc,
            "details": details
        }
