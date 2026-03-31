import re

with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    code = f.read()

# Replace the Chart.js configuration for FII/DII Chart to ensure `y1` has scale configuration correctly set and avoids flatlines.
# Chart.js version might need min/max dynamically, but maybe the API is returning an empty array for NIFTY, or string zeroes!
# Let's see what the backend is actually returning in `/api/market-activity/cash-flow`
