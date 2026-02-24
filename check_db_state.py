import sys
import os

# Add the repository root to sys.path
sys.path.append(os.getcwd())

from backend.infrastructure.db import engine
from sqlalchemy import text

def check_table_counts():
    try:
        with engine.connect() as conn:
            print("Checking table counts...")

            tables = ['import_logs', 'system_logs', 'bhavcopy_eq', 'bhavcopy_fo']
            for table_name in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"Table '{table_name}': {count} rows")
                except Exception as e:
                    print(f"Error checking table '{table_name}': {e}")

            # Check recent import logs specifically
            print("\nRecent Import Logs:")
            try:
                result = conn.execute(text("SELECT * FROM import_logs ORDER BY created_at DESC LIMIT 5"))
                rows = result.fetchall()
                if not rows:
                    print("No import logs found.")
                else:
                    for row in rows:
                        print(row)
            except Exception as e:
                print(f"Error checking import_logs: {e}")

    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    check_table_counts()
