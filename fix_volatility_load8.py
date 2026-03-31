# If it returned 500 JSON, then `const data = await res.json();` would work, and `data.detail` would exist!
# Then `if (data.detail) { alert(...) }` would popup an alert.
# The user said "No error, its dead button", which means NO alert!
# If NO alert popped up, either `volPreExpiryChart` failed to init, OR `res.json()` failed!
# Wait! In `script_workbench2.js`:
# `volPreExpiryChart = echarts.init(preExpiryChartDom, 'dark', { renderer: 'canvas' });`
# If `echarts.init` fails, it throws a JS error.
# Let's add a robust `try...catch` around the ENTIRE `loadVolatilityAnalysis` function!
import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

old_load = """async function loadVolatilityAnalysis() {
    console.log("Loading Volatility Analysis...");
    const symbol = document.getElementById('vol-analysis-symbol').value.toUpperCase() || 'NIFTY';"""

new_load = """async function loadVolatilityAnalysis() {
    console.log("Loading Volatility Analysis...");
    try {
        const symbol = document.getElementById('vol-analysis-symbol').value.toUpperCase() || 'NIFTY';"""

js = js.replace(old_load, new_load)

# Add closing bracket to the end of the function:
# We need to find the end of `loadVolatilityAnalysis`
end_index = js.find('async function loadCorporateActions()')
if end_index != -1:
    js = js[:end_index-1] + "} catch (e) { console.error('Error in loadVolatilityAnalysis:', e); alert('Error loading Volatility Analysis: ' + e.message); }\n" + js[end_index:]
    with open("backend/ui/static/js/script_workbench2.js", "w") as f:
        f.write(js)
    print("Wrapped loadVolatilityAnalysis in try/catch")
else:
    print("Could not find end of loadVolatilityAnalysis")
