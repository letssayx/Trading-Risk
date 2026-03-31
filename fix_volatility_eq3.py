import re

with open("backend/web/api/data/volatility_routes.py", "r") as f:
    code = f.read()

# Replace the incorrect fallback logic.
# It currently has `result = db.execute(query, {"symbol": symbol, "lookback": lookback_days}).fetchall()` inside an `except Exception`.
# The problem is that the first `except Exception:` catches exceptions, then runs `db.execute(query)` which fails for NIFTY because `bhavcopy_eq` returns empty result, NOT an exception!
# So `result` becomes `[]` without throwing an exception, and the `except Exception` block for `bhavcopy_eq` is NEVER triggered or it is, but it also returns `[]`.
# THEN it says `if not result and symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]: db.rollback()`
# Wait, if `result = []`, it enters the `if not result`.
# Inside it does `SELECT DISTINCT ON (trade_date) trade_date, close_price FROM bhavcopy_fo WHERE ticker_symb = 'NIFTY' AND instrument_type IN ('FUTIDX', 'FUTSTK') ORDER BY trade_date DESC, expiry_date ASC`
# And THAT query is failing because `DISTINCT ON` expressions must match initial `ORDER BY` expressions in Postgres!
# The initial `ORDER BY` expression is `trade_date DESC`. So it should be `DISTINCT ON (trade_date)`. But Postgres is picky about ASC/DESC.
# Actually, `DISTINCT ON (trade_date) trade_date` with `ORDER BY trade_date DESC` is fine, BUT `bhavcopy_fo` might not have `close_price` for that combination if `instrument_type` is legacy.
# The user's memory says: "When querying active futures data from BhavcopyFO, the instrument_type filter must include modern NSE codes ['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']"

# Let's fix the `DISTINCT ON` query to be completely robust.
old_query = """SELECT DISTINCT ON (trade_date) trade_date, close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK')
                ORDER BY trade_date DESC, expiry_date ASC
                LIMIT :lookback"""

new_query = """SELECT trade_date, MIN(close_price) as close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK', 'IDF', 'STF', 'FUTIVX', 'FUTIRC')
                GROUP BY trade_date
                ORDER BY trade_date DESC
                LIMIT :lookback"""

code = code.replace(old_query, new_query)

# And similarly for the other place in volatility_cone:
old_query2 = """SELECT DISTINCT ON (trade_date) trade_date, close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK')
                ORDER BY trade_date ASC, expiry_date ASC"""

new_query2 = """SELECT trade_date, MIN(close_price) as close_price
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK', 'IDF', 'STF', 'FUTIVX', 'FUTIRC')
                GROUP BY trade_date
                ORDER BY trade_date ASC"""

code = code.replace(old_query2, new_query2)

with open("backend/web/api/data/volatility_routes.py", "w") as f:
    f.write(code)
