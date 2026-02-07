from backend.core.indicators.technical import Indicator
import pandas as pd

class LiquidityCore(Indicator):
    """
    Tracks Global Liquidity: DXY and Fed Rate.
    """
    def compute(self, data: pd.DataFrame) -> dict:
        # Expects 'dxy_close', 'fed_rate' columns
        latest = data.iloc[-1]
        return {
            "dxy_trend": latest.get('dxy_close', 0) > data['dxy_close'].mean(),
            "fed_stress": latest.get('fed_rate', 0) > 5.0 # Threshold for tight liquidity
        }

class GlobalCommodities(Indicator):
    """
    Tracks LME and Precious Metals.
    """
    def compute(self, data: pd.DataFrame) -> dict:
        # Expects 'copper_lme', 'gold_spot'
        latest = data.iloc[-1]
        copper_chg = data['copper_lme'].pct_change().iloc[-1] if 'copper_lme' in data.columns else 0
        return {
            "metal_pulse": "Bullish" if copper_chg > 0.01 else "Bearish",
            "gold_rotation": latest.get('gold_spot', 0) > data['gold_spot'].rolling(20).mean().iloc[-1]
        }

class CorrelationMapping(Indicator):
    """
    Checks Global-Local Linkages.
    """
    def compute(self, data: pd.DataFrame) -> str:
        # Logic: If LME Copper > 1% and Nifty Metals < 0%, flag Gap.
        copper_chg = data['copper_lme'].pct_change().iloc[-1] if 'copper_lme' in data.columns else 0
        local_metal_chg = data['nifty_metal'].pct_change().iloc[-1] if 'nifty_metal' in data.columns else 0

        if copper_chg > 0.01 and local_metal_chg < 0:
            return "RELATIVE_VALUE_GAP"

        # Logic: DXY Up + FII Long = Divergence
        dxy_chg = data['dxy_close'].pct_change().iloc[-1] if 'dxy_close' in data.columns else 0
        fii_long = data['fii_net'].iloc[-1] > 0 if 'fii_net' in data.columns else False

        if dxy_chg > 0.005 and fii_long:
            return "HIGH_RISK_DIVERGENCE"

        return "SYNC"
