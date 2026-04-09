import sys
import os
import traceback
from sqlalchemy import text
from backend.infrastructure.db import engine

def main():
    try:
        with engine.connect() as conn:
            print("Fixing the oi_analysis_metrics table 'id' column sequence in Postgres...")

            sql = """
            CREATE SEQUENCE IF NOT EXISTS oi_analysis_metrics_id_seq;
            ALTER TABLE oi_analysis_metrics ALTER COLUMN id SET DEFAULT nextval('oi_analysis_metrics_id_seq');
            ALTER SEQUENCE oi_analysis_metrics_id_seq OWNED BY oi_analysis_metrics.id;
            SELECT setval('oi_analysis_metrics_id_seq', COALESCE((SELECT MAX(id)+1 FROM oi_analysis_metrics), 1), false);
            """

            conn.execute(text(sql))
            conn.commit()
            print("Successfully updated 'id' column to be auto-incrementing!")

    except Exception as e:
        print(f"Error applying fix: {e}")

if __name__ == "__main__":
    main()
