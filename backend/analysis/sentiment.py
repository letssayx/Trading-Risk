from typing import Dict, Optional, Tuple

def analyze_sentiment_flow(
    fii_net_cash: float, # Crores. Positive = Buy
    pcr: float, # Put-Call Ratio
    trin: float, # Arms Index
    price_change: float, # Percent change (e.g. 0.015)
    oi_change: float # Percent change (e.g. 0.05)
) -> str:
    """
    Analyzes Sentiment Flow to generate directional signals.

    Logic:
    - BUY (Long Build-Up):
        - FII Net Buying (> 0)
        - PCR < 1.0 (Oversold / Bullish Support?) - Actually High PCR > 1.0 is Bullish (Put writers active)?
          Wait, prompt says "If PCR is at extreme highs... warning".
          Standard interpretation: High PCR (>1.0) = Bullish (Put Volume > Call Volume, support building? Or Bearish/Hedging?)
          Let's use "Smart Money Sync": FII Buy + Price Up + OI Up (Long Build) is key.
          PCR: Low PCR (<0.7) usually Overbought/Complacent. High PCR (>1.5) Oversold/Panic or Hedging.
          Let's stick to FII + Price + OI as primary.

    - SELL (Short Build-Up):
        - FII Net Selling (< 0)
        - TRIN > 1.2 (Bearish/Panic Selling volume)
        - Price Down (< 0)
        - OI Up (> 0) (Short Build)
    """

    # Long Build: Price Up + OI Up + FII Buying
    if price_change > 0 and oi_change > 0 and fii_net_cash > 0:
        # Additional confirmation from PCR?
        # Let's say PCR > 0.8 (Healthy Support)
        if pcr > 0.8:
            return "BUY"

    # Short Build: Price Down + OI Up + FII Selling
    if price_change < 0 and oi_change > 0 and fii_net_cash < 0:
        # Additional confirmation from TRIN?
        # TRIN > 1.2 indicates selling pressure (Vol/Adv < Vol/Dec)
        if trin > 1.2:
            return "SELL"

    # Short Covering: Price Up + OI Down + FII Buying (Optional)
    if price_change > 0 and oi_change < 0 and fii_net_cash > 0:
        return "BUY_COVER"

    # Long Unwinding: Price Down + OI Down + FII Selling (Optional)
    if price_change < 0 and oi_change < 0 and fii_net_cash < 0:
        return "SELL_UNWIND"

    return "NEUTRAL"
