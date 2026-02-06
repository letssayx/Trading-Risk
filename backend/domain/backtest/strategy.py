from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class StrategyConfig:
    """
    Configuration for a backtest strategy.
    """
    name: str
    formula_trigger: str
    max_risk_per_trade: float
    allocation_pct: float = 0.1
    params: Dict[str, Any] = field(default_factory=dict)
