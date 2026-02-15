from typing import Dict, Any, List
from backend.domain.toolbox.base import BaseSovereignTool

class ConvergenceStrategy(BaseSovereignTool):
    """
    Convergence Strategy: Checks alignment between Turtle and Sentiment signals.
    """
    @property
    def name(self) -> str: return "Convergence Strategy"
    @property
    def category(self) -> str: return "Strategy"
    @property
    def description(self) -> str: return "Checks alignment between Turtle and Sentiment signals."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {turtle_signal: str, sentiment_signal: str}
        """
        turtle_signal = data.get("turtle_signal", "NEUTRAL")
        sentiment_signal = data.get("sentiment_signal", "NEUTRAL")

        # Normalize signals
        t_sig = turtle_signal.upper().strip()
        s_sig = sentiment_signal.upper().strip()

        # Simple mapping
        t_dir = 1 if t_sig == "BUY" else (-1 if t_sig == "SELL" else 0)

        s_dir = 0
        if s_sig in ["BUY", "BUY_COVER"]:
            s_dir = 1
        elif s_sig in ["SELL", "SELL_UNWIND"]:
            s_dir = -1

        # Check convergence
        if t_dir != 0 and t_dir == s_dir:
            return {
                "status": "HIGH_CONVICTION",
                "message": f"Both strategies align on {t_sig}",
                "score": 100
            }
        elif t_dir != 0 and s_dir == 0:
            return {
                "status": "MODERATE",
                "message": "Turtle Signal only",
                "score": 50
            }
        elif t_dir == 0 and s_dir != 0:
            return {
                "status": "MODERATE",
                "message": "Sentiment Signal only",
                "score": 50
            }
        elif t_dir != 0 and s_dir != 0 and t_dir != s_dir:
            return {
                "status": "CONFLICT",
                "message": "Strategies Disagree",
                "score": 0
            }

        return {
            "status": "NEUTRAL",
            "message": "No Signals",
            "score": 0
        }

def check_convergence(turtle_signal: str, sentiment_signal: str) -> Dict[str, Any]:
    """
    Wrapper for backward compatibility.
    """
    strategy = ConvergenceStrategy()
    return strategy.calculate({
        "turtle_signal": turtle_signal,
        "sentiment_signal": sentiment_signal
    })
