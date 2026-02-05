from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
from datetime import datetime

class ParticipantType(Enum):
    FII = "FII"   # Foreign Institutional Investors
    DII = "DII"   # Domestic Institutional Investors
    PRO = "PRO"   # Proprietary Traders
    CLIENT = "CLIENT" # Retail / HNI Clients
    COMMERCIAL = "COMMERCIAL" # Hedgers/Producers
    NON_COMMERCIAL = "NON_COMMERCIAL" # Speculators/Funds

@dataclass(frozen=True, kw_only=True)
class PositioningSnapshot:
    """Stores Large Position data by participant type."""
    id: str
    timestamp: datetime
    instrument_id: Optional[str] = None # None implies market-wide (e.g., Index aggregate)

    # Map of ParticipantType -> Net Long/Short contracts or value
    net_positions: Dict[ParticipantType, float] = field(default_factory=dict)

    # Detailed breakdown: ParticipantType -> {"long": X, "short": Y}
    long_short_breakdown: Dict[ParticipantType, Dict[str, float]] = field(default_factory=dict)

    metadata: Dict[str, str] = field(default_factory=dict)
