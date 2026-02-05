from dataclasses import dataclass
from datetime import date
from .instrument import Instrument
from .asset import UnderlyingAsset

@dataclass(frozen=True, kw_only=True)
class FutureContract(Instrument):
    """Future contract definition."""
    expiry: date
    underlying: UnderlyingAsset
    settlement_type: str  # e.g., "Cash", "Physical"
