from datetime import datetime, timedelta
from typing import Dict, Any

class LatencyMonitor:
    """
    Monitors data ingestion latency (Heartbeat).
    """
    def __init__(self, tolerance_ms: int = 500):
        self.tolerance_ms = tolerance_ms

    def check_latency(self, last_tick_time: datetime) -> Dict[str, Any]:
        now = datetime.utcnow()
        # Ensure last_tick_time is naive or aware consistent with now
        # Assuming UTC for both
        latency = (now - last_tick_time).total_seconds() * 1000

        status = "HEALTHY"
        if latency > self.tolerance_ms:
            status = "LAGGING"
        if latency > self.tolerance_ms * 5:
            status = "CRITICAL_DELAY"

        return {
            "latency_ms": latency,
            "status": status,
            "tolerance_ms": self.tolerance_ms
        }
