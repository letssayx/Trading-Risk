# Verify it updated
with open("backend/web/api/data/volatility_routes.py", "r") as f:
    code = f.read()
if "MIN(close_price)" in code:
    print("volatility queries patched")
else:
    print("not patched!")
