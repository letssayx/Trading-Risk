from typing import Dict

def calculate_index_hedge(
    portfolio_betas: Dict[str, float],
    portfolio_notional: Dict[str, float],
    index_price: float,
    index_lot_size: int,
    market_neutral_target: float = 0.0
) -> Dict[str, float]:
    """
    Calculates Beta-Weighted Index Short needed to neutralize systematic risk.
    Formula: Index_Lots = Sum(Pos_Value * Beta) / (Index_Price * Lot_Size)

    Args:
        portfolio_betas: Beta of each asset against Index.
        portfolio_notional: Dollar value (Price * Qty) of each position.
        index_price: Current index level (e.g. Nifty).
        index_lot_size: Lot size (e.g. 50).

    Returns:
        Dict with "Total_Beta_Exposure", "Lots_To_Short", "Hedge_Ratio".
    """
    total_beta_exposure = 0.0

    for asset, notional in portfolio_notional.items():
        beta = portfolio_betas.get(asset, 1.0) # Default to 1 if unknown
        total_beta_exposure += notional * beta

    index_contract_val = index_price * index_lot_size

    if index_contract_val <= 0:
        return {"Lots_To_Short": 0, "Exposure": 0}

    lots_needed = total_beta_exposure / index_contract_val

    # Negative lots means short
    # If total_beta_exposure is positive (Long Portfolio), we need to Short Index
    # If exposure is negative (Short Portfolio), we need to Long Index

    return {
        "total_beta_exposure": total_beta_exposure,
        "lots_to_hedge": round(lots_needed, 2), # Can trade fractional? Usually integer.
        "contracts_needed": int(round(lots_needed))
    }

def calculate_sentiment_hedge(
    base_hedge_contracts: int,
    fii_net_cash: float, # Positive = Buy, Negative = Sell (in Crores)
    pcr: float,
    trin: float
) -> Dict[str, int]:
    """
    Adjusts Hedge Ratio based on Sentiment.
    - If FII Net Sell (Fear) & Long Portfolio: Increase Hedge by 20%.
    - If PCR > 1.5 (Overbought? Or Oversold? High PCR usually Bullish? No, High PCR > 1.5 is Overbought/Froth).
    - If TRIN > 1.2 (Oversold/Fear? High TRIN usually Bearish/Panic).

    Prompt Logic:
    - "If FIIs are Net Sellers (Fear) ... increase Hedge Coverage by 20% (Over-hedging)."
    - "If TRIN > 1.2 (Overbought) or PCR is at extreme highs..." -> Warning.
    Wait, TRIN > 1.2 is usually OVERSOLD (Panic). TRIN < 0.5 is Overbought.
    Prompt says "TRIN > 1.2 (Overbought)". I will follow prompt literally, but flag potential confusion.
    Actually, usually High TRIN = Bearish/Selling pressure.

    Args:
        base_hedge_contracts: Calculated from Beta.
        fii_net_cash: Daily FII Net flow.
        pcr: Put-Call Ratio.
        trin: TRIN Index.

    Returns:
        Adjusted contracts.
    """
    adjustment_factor = 1.0
    reason = []

    # FII Logic
    if fii_net_cash < 0: # Net Sellers
        adjustment_factor += 0.20
        reason.append("FII Net Sell (Fear)")

    # PCR Logic (Extreme Highs -> Reversal Risk?)
    if pcr > 1.5:
        # Maybe increase hedge? Prompt says "Trigger Systematic Risk Warning".
        # Let's add 10% just to be safe? Or just flag it.
        # "trigger a 'Systematic Risk Warning' ... even if stock looks strong."
        reason.append("PCR Extreme High")

    # TRIN Logic
    if trin > 1.2:
        reason.append("TRIN > 1.2")

    final_contracts = int(base_hedge_contracts * adjustment_factor)

    return {
        "base_contracts": base_hedge_contracts,
        "adjusted_contracts": final_contracts,
        "adjustment_factor": adjustment_factor,
        "reasons": reason
    }
