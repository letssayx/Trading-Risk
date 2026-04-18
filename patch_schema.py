from backend.infrastructure.db import engine
from sqlalchemy import text

def add_columns():
    cols = [
        ("near_fut_close", "FLOAT"),
        ("next_fut_close", "FLOAT"),
        ("far_fut_close", "FLOAT"),
        ("delivery_pct_avg", "FLOAT"),
        ("highest_delivery_pct", "FLOAT"),
        ("eq_vol_avg", "FLOAT"),
        ("highest_eq_vol", "FLOAT"),
        ("z_score", "FLOAT")
    ]
    with engine.begin() as conn:
        for col_name, col_type in cols:
            try:
                conn.execute(text(f"ALTER TABLE daily_derivatives_analysis ADD COLUMN {col_name} {col_type};"))
                print(f"Added column {col_name}")
            except Exception as e:
                print(f"Skipping {col_name} (already exists or error): {e}")

if __name__ == '__main__':
    add_columns()
