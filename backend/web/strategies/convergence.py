from typing import Dict, Any, List

def check_convergence(
    turtle_signal: str,
    sentiment_signal: str
) -> Dict[str, Any]:
    """
    Checks if Turtle and Sentiment strategies are aligned.

    Args:
        turtle_signal: "BUY", "SELL", "NEUTRAL"
        sentiment_signal: "BUY", "SELL", "BUY_COVER", "SELL_UNWIND", "NEUTRAL"

    Returns:
        Dict with "convergence_status" (High/Low/None) and "conviction_score".
    """

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
