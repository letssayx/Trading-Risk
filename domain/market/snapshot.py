from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from domain.instruments.instrument import Instrument
from domain.market.positioning import PositioningSnapshot

@dataclass(frozen=True)
class InstrumentSnapshot:
    """Per-contract data derived from market snapshot."""
    instrument: Instrument
    timestamp: datetime
    price: float
    open_interest: Optional[float] = None
    volume: Optional[float] = None
    implied_volatility: Optional[float] = None
    greeks: Dict[str, float] = field(default_factory=dict)

    # Additional metadata or raw data points
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class MarketSnapshot:
    """Immutable view of derivative-specific market state at a time."""
    id: str
    timestamp: datetime
    # Map of instrument ID to its snapshot
    instruments: Dict[str, InstrumentSnapshot] = field(default_factory=dict)

    # Global or aggregate metrics (e.g., total OI for an underlying)
    aggregates: Dict[str, Any] = field(default_factory=dict)

    # Term structure summary, etc.
    term_structure: Dict[str, Any] = field(default_factory=dict)

    # Optional positioning data (e.g. Participant OI)
    positioning: Optional[PositioningSnapshot] = None

    def get_instrument_snapshot(self, instrument_id: str) -> Optional[InstrumentSnapshot]:
        return self.instruments.get(instrument_id)
