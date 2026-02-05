from typing import Dict, Any, Optional

def detect_institutional_buying(current_tick: Dict[str, Any], avg_volume_20: float) -> Optional[Dict[str, Any]]:
    """
    Detects large buy orders by comparing current volume against historical
    averages and identifying 'aggressive' price action.
    """
    volume = current_tick.get('volume', 0)
    close = current_tick.get('close', 0)
    vwap = current_tick.get('vwap', 0)
    quantity = current_tick.get('quantity', 0)

    if avg_volume_20 == 0:
        return None

    # 1. Volume Spike Detection (e.g., 3x average)
    is_vol_spike = volume > (avg_volume_20 * 3)

    # 2. Aggression Check: Price must be moving up with the volume
    is_price_aggressive = close > vwap

    # 3. Size Filtering: Only flag orders above a specific lot threshold
    is_institutional_size = quantity > 500 # Example lot threshold

    if is_vol_spike and is_price_aggressive and is_institutional_size:
        return {
            "type": "Large Buy Order",
            "impact": "Aggressive Institutional Entry",
            "volume_ratio": round(volume / avg_volume_20, 2),
            "large_orders": "Detected",
            "aggressor": "Buyer",
            "vol_spike": f"{round(volume / avg_volume_20, 1)}x"
        }

    return None
