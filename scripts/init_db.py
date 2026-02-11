"""
Initializes core database tables for the Trading-Risk engine.

Creates tables for:
- portfolios
- trades
- user_overrides
- risk_logs (simple audit log per trade/portfolio)

Uses DATABASE_URL from the environment (.env) so it matches your live config.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is on sys.path so `backend.*` imports work when this
# script is executed directly via `python scripts/init_db.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from backend.domain.common.base import Base
from backend.domain.portfolio.models import Portfolio, Trade  # noqa: F401  # ensure models are imported


def ensure_risk_logs_model():
    """
    Define a minimal RiskLog model if it does not already exist on Base.

    This avoids double-defining the model if later you move it into
    backend/domain/ and import it from there instead.
    """
    if "risk_logs" in Base.metadata.tables:
        return

    class RiskLog(Base):  # type: ignore[misc]
        __tablename__ = "risk_logs"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True)
        trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id"), nullable=True)

        event_type = Column(String, nullable=False)  # e.g. "MARGIN_CALL", "STOP_LOSS", "LIMIT_VIOLATION"
        severity = Column(String, nullable=False, default="INFO")  # e.g. "INFO", "WARN", "CRITICAL"
        message = Column(String, nullable=False)

        snapshot = Column(JSONB, default={})  # store VaR, greeks, exposure, etc.

        created_at = Column(DateTime, default=datetime.utcnow)

        # Optional relationships for easier querying (not strictly required)
        portfolio = relationship("Portfolio", backref="risk_logs")
        trade = relationship("Trade", backref="risk_logs")

    return


def main() -> None:
    # Load .env so DATABASE_URL is available
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Set it in your .env (or environment) before running scripts/init_db.py"
        )

    # Ensure RiskLog is attached to Base.metadata before create_all
    ensure_risk_logs_model()

    print(f"[init_db] Connecting using DATABASE_URL={database_url!r}")
    engine = create_engine(database_url)

    print("[init_db] Creating tables (if they do not exist) for:")
    print("         - portfolios")
    print("         - trades")
    print("         - user_overrides")
    print("         - risk_logs")

    Base.metadata.create_all(bind=engine)

    print("[init_db] Done. Schema is up to date.")


if __name__ == "__main__":
    main()

