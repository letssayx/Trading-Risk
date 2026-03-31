# The user issue also says "Load button feels like dead"
# Does `loadVolatilityAnalysis()` throw an error before it does anything?
# In `script_workbench2.js`:
import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js_code = f.read()

# Find `loadVolatilityAnalysis` and see what it references.
# It references `document.getElementById('vol-analysis-symbol')`
# AND `document.getElementById('vol-analysis-expiry-type')`
# AND `document.getElementById('vol-analysis-lookback')`
# AND `document.getElementById('vol-analysis-box-days')`
# Are all of these IDs present in `workbench.html`?
with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

print("symbol:", "id=\"vol-analysis-symbol\"" in html)
print("expiry-type:", "id=\"vol-analysis-expiry-type\"" in html)
print("lookback:", "id=\"vol-analysis-lookback\"" in html)
print("box-days:", "id=\"vol-analysis-box-days\"" in html)

# What about the chart dom elements?
print("pre-expiry-chart:", "id=\"vol-pre-expiry-chart\"" in js_code and "id=\"vol-pre-expiry-chart\"" in html)
print("cone-chart:", "id=\"vol-cone-chart\"" in js_code and "id=\"vol-cone-chart\"" in html)
