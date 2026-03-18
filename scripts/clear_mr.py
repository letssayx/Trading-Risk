import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import DailyDerivativesAnalysis

def clear_data():
    try:
        db = SessionLocal()
        print("Connecting to database...")
        num_deleted = db.query(DailyDerivativesAnalysis).delete()
        db.commit()
        print(f"Successfully deleted {num_deleted} records from daily_derivatives_analysis.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_data()
