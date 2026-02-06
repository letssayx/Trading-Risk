from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.strategies.models import Strategy
import uuid

class StrategyRegistry:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_strategy(self, user_id: uuid.UUID, name: str, code: str, config: Dict[str, Any]) -> Strategy:
        """
        Saves a new strategy version.
        """
        print(f"Saving Strategy: {name}")
        strategy = Strategy(
            user_id=user_id,
            name=name,
            source_code=code,
            config_json=config,
            version=1
        )
        self.db_session.add(strategy)
        self.db_session.commit()
        self.db_session.refresh(strategy)
        return strategy

    def load_strategy(self, name: str) -> Optional[Strategy]:
        """
        Loads strategy metadata.
        """
        print(f"Loading Strategy: {name}")
        return self.db_session.query(Strategy).filter(Strategy.name == name).first()
