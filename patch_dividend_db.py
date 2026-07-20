import sys
import os

print("""
######################################################################
# RUN THIS SCRIPT ON YOUR HOST MACHINE (WHERE YOUR VENV/DB IS)
######################################################################

from backend.infrastructure.db import engine
from sqlalchemy import text

def patch_db():
    with engine.connect() as conn:
        commands = [
            "ALTER TABLE dividend_databank ADD COLUMN IF NOT EXISTS eps FLOAT;",
            "ALTER TABLE dividend_databank ADD COLUMN IF NOT EXISTS dps FLOAT;",
            "ALTER TABLE dividend_databank ADD COLUMN IF NOT EXISTS dividend_yield FLOAT;",
            "ALTER TABLE dividend_databank ADD COLUMN IF NOT EXISTS payout_ratio FLOAT;",
            "ALTER TABLE dividend_databank ADD COLUMN IF NOT EXISTS agm_announcement_date DATE;",
            "ALTER TABLE dividend_databank ADD COLUMN IF NOT EXISTS agm_date DATE;"
        ]
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                print(f"Successfully ran: {cmd}")
            except Exception as e:
                print(f"Skipping (might already exist or error): {e}")
        conn.commit()
    print("Database patched successfully!")

if __name__ == "__main__":
    patch_db()
""")
