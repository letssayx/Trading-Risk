# The user issue says "Nifty is still a flat line in market activity tab in all charts"
# Look at the query for NIFTY prices in `cash_flow`:
# `SELECT trade_date, close_price FROM bhavcopy_fo WHERE ticker_symb = 'NIFTY' AND instrument_type IN ('FUTIDX', 'FUTSTK')`
# This query only gets NIFTY from `bhavcopy_fo` futures!
# What if NIFTY has no futures data for those dates because of the failed downloads, but maybe `bhavcopy_eq` or `bhavcopy_idx` has it?
# Or what about `nifty_close_list = [nifty_prices.get(d.date(), 0.0) for d in pivot.index]`?
# If `nifty_prices` is mostly missing, it returns 0.0.
# A chart with [25000, 0, 0, 25100, 0] will look flat because 0 forces the axis scale to go down to 0, squashing the 25000 variation.
# Memory says: "calculate the minimum and maximum values of the dataset directly in JavaScript prior to chart initialization and explicitly set y.min and y.max in the scales configuration". We did that!
# Wait, look at the JavaScript logic I added:
# `const validNifty = niftyData.filter(v => v !== null && !isNaN(v));`
# BUT `nifty_close_list` has `0.0` for missing dates! `0.0 !== null` and `!isNaN(0.0)`.
# So `absMin` becomes `0`. Then `minNifty` becomes `-pad` (near 0). The chart flattens!
# To fix this, in backend we should return `None` instead of `0.0` for missing values, and in frontend filter out `v > 0`.

import re
with open("backend/web/api/analysis_routes.py", "r") as f:
    code = f.read()

# Fix the cash flow query to return None instead of 0.0
code = code.replace("nifty_close_list = [nifty_prices.get(d.date(), 0.0) for d in pivot.index]", "nifty_close_list = [nifty_prices.get(d.date(), None) for d in pivot.index]")

with open("backend/web/api/analysis_routes.py", "w") as f:
    f.write(code)
