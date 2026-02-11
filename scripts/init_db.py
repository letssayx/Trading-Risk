"""
Initializes core database tables for the Trading-Risk engine.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.domain.common.base import Base
from backend.domain.portfolio.models import Portfolio, Trade  # noqa: F401

def ensure_risk_logs_model():
    if "risk_logs" in Base.metadata.tables:
        return

    class RiskLog(Base):
        __tablename__ = "risk_logs"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True)
        trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id"), nullable=True)
        event_type = Column(String, nullable=False)
        severity = Column(String, nullable=False, default="INFO")
        message = Column(String, nullable=False)
        snapshot = Column(JSONB, default={})
        created_at = Column(DateTime, default=datetime.utcnow)
        
        portfolio = relationship("Portfolio", backref="risk_logs")
        trade = relationship("Trade", backref="risk_logs")

def main() -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set in your .env file.")

    ensure_risk_logs_model()

    print(f"[init_db] Connecting to database...")
    engine = create_engine(database_url)

    print("[init_db] Creating tables: portfolios, trades, risk_logs...")
    Base.metadata.create_all(bind=engine)
    print("[init_db] Done. Schema is up to date.")

if __name__ == "__main__":
    main()