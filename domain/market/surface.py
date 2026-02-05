from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Tuple
from domain.instruments.asset import UnderlyingAsset

@dataclass(frozen=True)
class DerivativeSurface:
    """Container for options surface attributes (volatility surface, skew summaries)."""
    underlying: UnderlyingAsset
    timestamp: datetime

    # Volatility surface data: Map of (expiry, strike) -> implied_volatility
    volatility_surface: Dict[Tuple[date, float], float] = field(default_factory=dict)

    # Skew summaries: Map of expiry -> skew metric (e.g., 25D RR)
    skew_summaries: Dict[date, float] = field(default_factory=dict)

    # Term structure of ATM volatility: Map of expiry -> atm_vol
    term_structure: Dict[date, float] = field(default_factory=dict)
