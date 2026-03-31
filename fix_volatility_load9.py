import re

with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

# Replace the start of the function
old_load = """async function loadVolatilityAnalysis() {
    console.log("Loading Volatility Analysis...");
    const symbol = document.getElementById('vol-analysis-symbol').value.toUpperCase() || 'NIFTY';"""

new_load = """async function loadVolatilityAnalysis() {
    console.log("Loading Volatility Analysis...");
    try {
        const symbol = document.getElementById('vol-analysis-symbol').value.toUpperCase() || 'NIFTY';"""

if old_load in js:
    js = js.replace(old_load, new_load)

    # The function ends right before `function exportTableToCSV` (around line 3474)
    # Let's find the closing brace.
    idx = js.find('function exportTableToCSV')
    if idx != -1:
        # Find the last closing brace before idx
        brace_idx = js.rfind('}', 0, idx)
        js = js[:brace_idx] + "    } catch (e) { console.error('Error in loadVolatilityAnalysis:', e); alert('Error loading Volatility Analysis: ' + e.message); }\n" + js[brace_idx:]

        with open("backend/ui/static/js/script_workbench2.js", "w") as f:
            f.write(js)
        print("Wrapped successfully")
    else:
        print("Could not find exportTableToCSV")
else:
    print("Could not find old_load")
