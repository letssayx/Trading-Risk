from typing import Optional, Dict, Any
from backend.strategies.models import StrategyModel

class StrategyRegistry:
    def __init__(self, db_session=None):
        self.db_session = db_session

    def save_strategy(self, name: str, code: str, config: Dict[str, Any]):
        """
        Saves a new strategy version.
        """
        print(f"Saving Strategy: {name}")
        # In prod: session.add(StrategyModel(...))

    def load_strategy(self, name: str) -> Optional[StrategyModel]:
        """
        Loads strategy metadata.
        """
        print(f"Loading Strategy: {name}")
        return None
