import os
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost/turtle')
with engine.connect() as conn:
    print("Test Expiry only CTE:")
    res = conn.execute(text("""
        WITH expiries AS (
            SELECT DISTINCT expiry_date
            FROM bhavcopy_fo
            WHERE ticker_symb = 'NIFTY'
        ),
        valid_dates AS (
            SELECT DISTINCT trade_date
            FROM bhavcopy_fo
            WHERE ticker_symb = 'NIFTY'
              AND trade_date IN (SELECT expiry_date FROM expiries)
        )
        SELECT trade_date FROM valid_dates ORDER BY trade_date DESC LIMIT 10
    """)).fetchall()
    print("CTE result:", res)

    print("\nTest simpler join:")
    res2 = conn.execute(text("""
        SELECT DISTINCT trade_date
        FROM bhavcopy_fo
        WHERE ticker_symb = 'NIFTY'
        AND trade_date = expiry_date
        ORDER BY trade_date DESC LIMIT 10
    """)).fetchall()
    print("Join result:", res2)
