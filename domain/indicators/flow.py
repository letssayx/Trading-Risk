from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional

class FlowType(Enum):
    LONG_BUILDUP = "LONG_BUILDUP"       # Price Up, OI Up
    SHORT_COVERING = "SHORT_COVERING"   # Price Up, OI Down
    SHORT_BUILDUP = "SHORT_BUILDUP"     # Price Down, OI Up
    LONG_UNWIND = "LONG_UNWIND"         # Price Down, OI Down
    NEUTRAL = "NEUTRAL"

@dataclass(frozen=True, kw_only=True)
class FlowResult:
    """Structured output of Price + OI + Participant flow analysis."""
    flow_type: FlowType
    price_change_pct: float
    oi_change_pct: float

    # Optional: Confirmation from large participant positioning
    institutional_confirmation: bool = False

    # Metadata for interpretation
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
