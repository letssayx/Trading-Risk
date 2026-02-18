from typing import Dict, Any
from backend.domain.toolbox.base import BaseSovereignTool
from backend.analysis.greeks import interpret_iv_skew
from backend.strategies.vol_arb import VolArbitrageStrategy

class VolatilitySurfaceTool(BaseSovereignTool):
    """
    Analyzes Volatility Surface (Skew & Term Structure).
    """
    @property
    def name(self) -> str: return "Volatility Surface Tool"
    @property
    def category(self) -> str: return "Indicator"
    @property
    def description(self) -> str: return "Analyzes IV Skew and Term Structure (Calendar Spreads)."

    def calculate(self, data: Dict[str, float]) -> Dict[str, Any]:
        """
        data: {iv_call, iv_put, atm_iv, iv_near, iv_far}
        """
        # Skew
        skew_res = interpret_iv_skew(
            data.get("iv_call", 0),
            data.get("iv_put", 0),
            data.get("atm_iv", 0)
        )

        # Term Structure
        term_res = VolArbitrageStrategy().calculate({
            "iv_near": data.get("iv_near", 0),
            "iv_far": data.get("iv_far", 0)
        })

        return {
            "skew_analysis": skew_res,
            "term_structure": term_res
        }
