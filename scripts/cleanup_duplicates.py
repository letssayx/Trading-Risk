from sqlalchemy.orm import Session
import os
import sys

# Setup path and database connection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction

db: Session = SessionLocal()

try:
    print("Finding synthesized corporate actions...")

    # In the original nse_importer.py, the exact format used was:
    # f"Dividend ({r.get('purpose', '')})".strip()
    # OR
    # f"Dividend - Record date not yet declared ({r.get('purpose', '')})".strip()

    # We will fetch all dividends and delete the ones that perfectly match this exact string template.
    # We use a broader query first, then filter strictly in Python to be 100% safe.
    records = db.query(CorporateAction).filter(
        CorporateAction.purpose.like("Dividend %")
    ).all()

    deleted_count = 0
    for r in records:
        purpose = r.purpose or ""
        # The synthesized strings start with "Dividend" or "Dividend - Record date" and ALWAYS end with a closing parenthesis ')'
        # AND contain an opening parenthesis '('
        if purpose.startswith("Dividend (") and purpose.endswith(")"):
            db.delete(r)
            deleted_count += 1
        elif purpose.startswith("Dividend - Record date not yet declared (") and purpose.endswith(")"):
            db.delete(r)
            deleted_count += 1

    db.commit()
    print(f"Cleanup complete. Deleted {deleted_count} synthesized corporate actions.")

except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
