from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class Scenario:
    """Parameterized market move description."""
    name: str
    description: str
    parameters: Dict[str, Any]  # e.g., {"spot_move": -0.05, "vol_shock": 0.02}

@dataclass(frozen=True)
class ScenarioResult:
    """Output of applying scenario to portfolio or idea."""
    scenario: Scenario
    pnl_impact: float
    # Detailed breakdown if needed
    details: Dict[str, Any] = field(default_factory=dict)
