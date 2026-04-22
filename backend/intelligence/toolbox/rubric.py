from typing import Dict, Any, Optional

class ScoringService:
    """
    Standalone Service for scoring portfolios or strategies based on a Rubric.
    """
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # Default Weights
        self.weights = weights or {
            "sharpe_ratio": 0.4,
            "sortino_ratio": 0.3,
            "governance_pass": 0.3
        }

    def calculate_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a score (0-100) based on input metrics.
        metrics: {"sharpe_ratio": 1.5, "sortino_ratio": 2.0, "governance_status": "ACCEPTED"}
        """
        score = 0.0
        details = {}

        # Sharpe (Target > 1.0)
        sharpe = metrics.get("sharpe_ratio", 0.0)
        sharpe_score = min(sharpe * 50, 100) # Cap at 100 for Sharpe=2
        score += sharpe_score * self.weights.get("sharpe_ratio", 0.0)
        details["sharpe_contrib"] = sharpe_score

        # Sortino (Target > 1.5)
        sortino = metrics.get("sortino_ratio", 0.0)
        sortino_score = min(sortino * 40, 100) # Cap at 100 for Sortino=2.5
        score += sortino_score * self.weights.get("sortino_ratio", 0.0)
        details["sortino_contrib"] = sortino_score

        # Governance
        gov = metrics.get("governance_status", "REJECTED")
        gov_score = 100.0 if gov == "ACCEPTED" else 0.0
        score += gov_score * self.weights.get("governance_pass", 0.0)
        details["governance_contrib"] = gov_score

        return {
            "total_score": round(score, 2),
            "breakdown": details,
            "grade": self._get_grade(score)
        }

    def _get_grade(self, score: float) -> str:
        if score >= 90: return "A+"
        if score >= 80: return "A"
        if score >= 70: return "B"
        if score >= 60: return "C"
        return "F"

class StandardAlphaScorecard(ScoringService):
    """
    OOTB Standard Rubric.
    """
    pass
