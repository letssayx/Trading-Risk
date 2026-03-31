import re

with open("backend/web/api/data/volatility_routes.py", "r") as f:
    code = f.read()

# Make sure `get_volatility_cone` also uses `MIN(close_price)` properly.
# The user issue also said "Volatility analysis is empty, check screenshot".
# If Volatility is empty, maybe `historical_index_data` doesn't exist, and `bhavcopy_eq` returns nothing for NIFTY.
# But `NIFTY` is an index! So the fallback `bhavcopy_fo` should kick in.
# BUT wait! Look at the `bhavcopy_fo` fallback in `get_volatility_cone`:
# `query = text("""SELECT DISTINCT ON (trade_date) trade_date, close_price FROM bhavcopy_fo WHERE ticker_symb = :symbol AND instrument_type IN ('FUTIDX', 'FUTSTK') ORDER BY trade_date ASC, expiry_date ASC""")`
# I just patched that.
# Let's check `get_pre_expiry_action` line 198:
# `if not result and symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:`
# What if it's "NIFTY50"? Or "BANKEX"? We should just use the `bhavcopy_fo` fallback unconditionally if `result` is empty!
code = code.replace('if not result and symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:', 'if not result:')

with open("backend/web/api/data/volatility_routes.py", "w") as f:
    f.write(code)
