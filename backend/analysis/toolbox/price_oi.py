from typing import Dict, Any
from backend.domain.toolbox.base import BaseSovereignTool
from backend.intelligence.sentiment_flow import analyze_sentiment_flow

class PriceOIQuadrantTool(BaseSovereignTool):
    """
    Analyzes Market Structure using Price vs Open Interest Quadrants.
    1. Long Build-Up (Price Up, OI Up)
    2. Short Build-Up (Price Down, OI Up)
    3. Short Covering (Price Up, OI Down)
    4. Long Unwinding (Price Down, OI Down)
    """
    @property
    def name(self) -> str: return "Price-OI Visualizer"
    @property
    def category(self) -> str: return "Indicator" # Or Analysis
    @property
    def description(self) -> str: return "Quadrant Analysis: Long Build, Short Build, Covering, Unwinding."

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        data: {
            "price_change": float, # % change (e.g. 0.01)
            "oi_change": float,    # % change (e.g. 0.05)
            "fii_net": float,      # Optional context
            "pcr": float,          # Optional context
            "trin": float          # Optional context
        }
        """
        price_chg = data.get("price_change", 0.0)
        oi_chg = data.get("oi_change", 0.0)
        fii = data.get("fii_net", 0.0)
        pcr = data.get("pcr", 1.0)
        trin = data.get("trin", 1.0)

        # Determine Quadrant
        quadrant = "Neutral"
        if price_chg > 0 and oi_chg > 0:
            quadrant = "Long Build-Up"
        elif price_chg < 0 and oi_chg > 0:
            quadrant = "Short Build-Up"
        elif price_chg > 0 and oi_chg < 0:
            quadrant = "Short Covering"
        elif price_chg < 0 and oi_chg < 0:
            quadrant = "Long Unwinding"

        # Get signal from Sentiment Logic
        signal = analyze_sentiment_flow(fii, pcr, trin, price_chg, oi_chg)

        return {
            "quadrant": quadrant,
            "signal": signal,
            "interpretation": f"{quadrant} with {signal} Sentiment"
        }
