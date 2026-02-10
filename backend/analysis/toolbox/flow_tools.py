from typing import Dict, Any
from backend.domain.toolbox.base import BaseSovereignTool

class InstitutionalPulse(BaseSovereignTool):
    """
    Fingerprints Institutional Flow (FII/DII).
    """
    @property
    def name(self) -> str: return "Institutional Pulse"
    @property
    def category(self) -> str: return "Indicator"
    @property
    def description(self) -> str: return "Tracks Smart Money Flow vs Retail."

    def calculate(self, data: Dict[str, float]) -> Dict[str, Any]:
        """
        data: {fii_net, dii_net, retail_net}
        """
        fii = data.get("fii_net", 0)
        retail = data.get("retail_net", 0)

        sentiment = "NEUTRAL"
        if fii > 0 and retail < 0:
            sentiment = "SMART_MONEY_LONG"
        elif fii < 0 and retail > 0:
            sentiment = "SMART_MONEY_SHORT"

        return {
            "flow_sentiment": sentiment,
            "net_institutional": fii + data.get("dii_net", 0)
        }
