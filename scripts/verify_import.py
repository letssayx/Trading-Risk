from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
import sys
import os
from datetime import date, datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.domain.market.models import Bhavcopy
from backend.ingest.nse_models import BhavcopyEQ, BhavcopyFO, FAOParticipantOI, FOVolatility
from backend.models.audit import SystemLog
from backend.infrastructure.db import SessionLocal

def verify_import():
    import os
    # Override DATABASE_URL for verification script if not set correctly
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "postgresql://turtle_admin:turtle_pass@timescaledb:5432/turtle_terminal"

    # Re-create engine with new URL if needed, but SessionLocal is already bound.
    # So we need to create a new session factory here.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(os.environ["DATABASE_URL"])
    SessionLocalOverride = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocalOverride()
    try:
        # Check Bhavcopy (Legacy)
        legacy_counts = db.query(Bhavcopy.trade_date, func.count(Bhavcopy.id)).group_by(Bhavcopy.trade_date).all()
        print("\n--- Legacy Bhavcopy Counts ---")
        for dt, count in legacy_counts:
            print(f"{dt}: {count}")
        if not legacy_counts:
            print("No data in legacy Bhavcopy.")

        # Check BhavcopyEQ (New)
        eq_counts = db.query(BhavcopyEQ.trade_date, func.count(BhavcopyEQ.id)).group_by(BhavcopyEQ.trade_date).all()
        print("\n--- New BhavcopyEQ Counts ---")
        for dt, count in eq_counts:
            print(f"{dt}: {count}")
        if not eq_counts:
            print("No data in BhavcopyEQ.")

        # Check BhavcopyFO (New)
        fo_counts = db.query(BhavcopyFO.trade_date, func.count(BhavcopyFO.id)).group_by(BhavcopyFO.trade_date).all()
        print("\n--- New BhavcopyFO Counts ---")
        for dt, count in fo_counts:
            print(f"{dt}: {count}")
        if not fo_counts:
            print("No data in BhavcopyFO.")

        # Check FAOParticipantOI
        oi_counts = db.query(FAOParticipantOI.trade_date, func.count(FAOParticipantOI.id)).group_by(FAOParticipantOI.trade_date).all()
        print("\n--- FAOParticipantOI Counts ---")
        for dt, count in oi_counts:
            print(f"{dt}: {count}")
        if not oi_counts:
            print("No data in FAOParticipantOI.")

        # Check System Logs
        log_counts = db.query(SystemLog.timestamp, SystemLog.level, SystemLog.message).order_by(SystemLog.timestamp.desc()).limit(10).all()
        print("\n--- Recent System Logs ---")
        for log in log_counts:
            print(f"{log.timestamp} [{log.level}]: {log.message}")
        if not log_counts:
            print("No system logs found.")

    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_import()
