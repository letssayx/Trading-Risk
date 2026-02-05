from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from .measure import RiskMeasure
from .scenario import ScenarioResult

@dataclass(frozen=True)
class RiskReport:
    """Container for measures, scenarios, and assumptions used."""
    timestamp: datetime
    entity_id: str  # Portfolio ID or Trade Idea ID
    measures: List[RiskMeasure] = field(default_factory=list)
    scenario_results: List[ScenarioResult] = field(default_factory=list)
    assumptions: Dict[str, Any] = field(default_factory=dict)
