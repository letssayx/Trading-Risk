from typing import Dict, Any

class BlockTradeScanner:
    """
    Flags trades exceeding X% of average volume.
    """
    def scan(self, tick_data: Dict[str, Any], avg_volume: float, threshold_pct: float = 300) -> Dict[str, Any]:
        vol = tick_data.get('volume', 0)
        if avg_volume > 0 and (vol / avg_volume) * 100 > threshold_pct:
            return {
                "signal": "BLOCK_TRADE",
                "volume": vol,
                "ratio": round(vol/avg_volume, 2),
                "rationale": f"Volume {vol} is {round(vol/avg_volume, 1)}x average."
            }
        return {}
