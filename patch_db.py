import os
from sqlalchemy.orm import Session
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction
from backend.ingest.field_mapper import FieldMapper
from typing import Optional

def run_patch():
    db: Session = SessionLocal()
    try:
        # Fetch all corporate actions
        actions = db.query(CorporateAction).filter(
            CorporateAction.purpose != None
        ).all()

        updated_count = 0
        for action in actions:
            if not action.purpose:
                continue

            # Attempt to parse
            amount, div_type = FieldMapper._parse_dividend(action.purpose, action.face_value)

            # Check if an update is needed
            needs_update = False
            if amount != action.parsed_dividend_amount:
                action.parsed_dividend_amount = amount
                needs_update = True

            if div_type and div_type != action.dividend_type:
                action.dividend_type = div_type
                needs_update = True

            if needs_update:
                updated_count += 1

        if updated_count > 0:
            db.commit()
            print(f"Successfully updated {updated_count} rows in CorporateAction.")
        else:
            print("No rows needed updating.")

    except Exception as e:
        print(f"Error updating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_patch()
