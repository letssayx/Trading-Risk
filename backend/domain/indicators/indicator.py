from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class Indicator:
    """Contract/Metadata for any indicator."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"

@dataclass(frozen=True)
class IndicatorResult:
    """Value plus provenance."""
    indicator: Indicator
    timestamp: datetime
    value: Any  # The actual result (float, dict, etc.)
    snapshot_id: str # Link back to the specific MarketSnapshot

    # Provenance
    inputs_hash: Optional[str] = None # Identifying specific data subset used
    computation_context: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class IndicatorSet:
    """Structured collection of results for an asset/expiry/segment."""
    entity_id: str  # ID of the asset/expiry/segment
    timestamp: datetime
    results: Dict[str, IndicatorResult] = field(default_factory=dict)
