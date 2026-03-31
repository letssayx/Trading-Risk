# If it's "dead", it's possible `volPreExpiryChart` or `volConeChart` are not defined globally, or `loadVolatilityAnalysis` has a syntax error!
# Let's inspect `script_workbench2.js` line 3271: `let volPreExpiryChart = null;`
# `let volConeChart = null;`
import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

# Let's see if there's any obvious syntax error around `loadVolatilityAnalysis`.
lines = js.split('\n')
start = -1
for i, line in enumerate(lines):
    if "async function loadVolatilityAnalysis()" in line:
        start = i
        break

if start != -1:
    print("\n".join(lines[start:start+50]))
