import re

with open("backend/web/api/analysis_routes.py", "r") as f:
    code = f.read()

# Make sure all .get(..., 0.0) for nifty are replaced
code = code.replace("nifty_prices_map.get(d.date(), 0.0)", "nifty_prices_map.get(d.date(), None)")
code = code.replace("nifty_prices.get(d.date(), 0.0)", "nifty_prices.get(d.date(), None)")

with open("backend/web/api/analysis_routes.py", "w") as f:
    f.write(code)
