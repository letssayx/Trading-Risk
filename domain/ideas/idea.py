from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from domain.instruments.instrument import Instrument
from domain.indicators.indicator import IndicatorResult
from domain.risk.report import RiskReport

class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL" # e.g. delta neutral strategies

@dataclass(frozen=True)
class TradeRationale:
    """Explanation, evidence links, and indicator references."""
    summary: str
    evidence: List[IndicatorResult] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    risk_narrative: Optional[str] = None # Plain text explanation of key risks

@dataclass(frozen=True)
class IdeaConstraint:
    """Boundary conditions (liquidity, expiry windows, risk tolerance)."""
    min_liquidity: float
    max_risk: float
    horizon: str # e.g., "Intraday", "Swing"
    required_conditions: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class TradeIdea:
    """Proposed trade structure."""
    id: str
    user_id: str # Author of the idea
    timestamp: datetime
    instruments: List[Instrument]
    direction: TradeDirection
    rationale: TradeRationale
    constraints: IdeaConstraint

    # Conditional entry/exit parameters
    entry_conditions: Dict[str, Any] = field(default_factory=dict)
    exit_conditions: Dict[str, Any] = field(default_factory=dict)

    # Attached risk analysis
    risk_summary: Optional[RiskReport] = None

    status: str = "PROPOSED" # PROPOSED, VALIDATED, REJECTED
