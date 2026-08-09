from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL", "postgresql://jules:jules@localhost:5432/finance")
engine = create_engine(db_url)

def add_columns():
    with engine.begin() as conn:
        print("Checking/Adding columns to dividend_databank...")

        columns = [
            ("agm_announcement_date", "DATE"),
            ("agm_date", "DATE"),
            ("eps", "FLOAT"),
            ("net_profit", "FLOAT"),
            ("dps", "FLOAT"),
            ("delta_dps", "FLOAT"),
            ("delta_eps", "FLOAT"),
            ("fy_total", "FLOAT"),
        ]

        for col_name, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE dividend_databank ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                print(f"Added/Verified column {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS financial_results (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    period VARCHAR(50),
                    period_end_date DATE,
                    basic_eps FLOAT,
                    diluted_eps FLOAT,
                    net_profit FLOAT,
                    attachment_url VARCHAR(1000)
                );
            """))
            # Make sure it's an underlying hypertable if required by TimescaleMixin in your real db
            print("Created financial_results table")
        except Exception as e:
            print(f"Error creating financial_results table: {e}")

        print("Done!")

if __name__ == "__main__":
    add_columns()
