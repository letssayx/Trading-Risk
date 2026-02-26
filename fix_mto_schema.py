from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Checking mto_delivery schema...")
    # Check current type
    result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'mto_delivery' AND column_name = 'quantity_traded'"))
    row = result.fetchone()
    if row:
        print(f"Current type of quantity_traded: {row[0]}")

    print("Altering mto_delivery columns to BIGINT...")
    try:
        conn.execute(text("ALTER TABLE mto_delivery ALTER COLUMN quantity_traded TYPE BIGINT"))
        conn.execute(text("ALTER TABLE mto_delivery ALTER COLUMN deliverable_qty TYPE BIGINT"))
        conn.commit()
        print("Schema update successful.")
    except Exception as e:
        print(f"Schema update failed: {e}")
