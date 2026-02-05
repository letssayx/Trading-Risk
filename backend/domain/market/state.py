from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from backend.domain.indicators.indicator import IndicatorResult

class SentimentSignal(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    UNCERTAIN = "UNCERTAIN"

@dataclass(frozen=True)
class MarketStateEvidence:
    """Links indicators to state with reasoning metadata."""
    description: str
    supporting_indicators: List[IndicatorResult] = field(default_factory=list)
    reasoning: Optional[str] = None

@dataclass(frozen=True)
class MarketState:
    """Descriptive, auditable classification of market environment."""
    name: str  # e.g., "Risk-On", "Short Squeeze"
    timestamp: datetime
    sentiment: SentimentSignal
    evidence: List[MarketStateEvidence] = field(default_factory=list)

    # Probability or confidence score if applicable
    confidence: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)
