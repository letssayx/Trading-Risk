# If it's defined at the top level and it's "dead", it means execution silently stops.
# Let's inspect `loadVolatilityAnalysis` further.
# "No error, its dead button".
# What if it's NOT fetching because `await fetch(...)` is throwing an error that IS caught but not logged, OR the URL is wrong, OR the button `onclick="loadVolatilityAnalysis()"` is literally doing nothing because `loadVolatilityAnalysis` is undefined?
# Wait! In HTML: `onclick="loadVolatilityAnalysis()"`
# Let's check the button element. `workbench.html` line 1438: `<button class="btn btn-primary" onclick="loadVolatilityAnalysis()">Load Volatility</button>`
# If the button doesn't do anything, maybe `id="deriv-tab-optanalysis"` is NEVER DISPLAYED?
# The user said "Volatility. analysis is empty, check screenshot".
# Ah! "empty" means they OPENED the tab, so it displayed! And they clicked "Load Volatility", and NOTHING happened.
# Why?
# Is `loadVolatilityAnalysis` getting called?
# Let's add an explicit `console.log("Loading Volatility...")` and `alert` or just check `fetch`.
import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

# I will add a `console.log` right at the start.
js = js.replace('async function loadVolatilityAnalysis() {', 'async function loadVolatilityAnalysis() {\n    console.log("Loading Volatility Analysis...");')

with open("backend/ui/static/js/script_workbench2.js", "w") as f:
    f.write(js)
