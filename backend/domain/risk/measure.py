from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class RiskMeasure:
    """Contract for computed risk output."""
    name: str  # e.g., "VaR 95%", "Delta Exposure"
    value: float
    unit: str # e.g., "USD", "Delta"
    methodology: str # e.g., "Historical Simulation", "Parametric"
    parameters: Dict[str, Any] = field(default_factory=dict)
