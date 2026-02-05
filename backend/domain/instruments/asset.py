from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class UnderlyingAsset:
    """Linkable entity for futures and options."""
    symbol: str
    name: str
    asset_class: str  # e.g., "Equity", "Commodity", "Index"
    exchange: Optional[str] = None
