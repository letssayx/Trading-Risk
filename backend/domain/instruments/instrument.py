from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True, kw_only=True)
class Instrument:
    """Base abstraction for all tradable derivatives."""
    id: str
    symbol: str
    exchange: str
    currency: str
    contract_size: float
    tick_size: float
    description: Optional[str] = None
