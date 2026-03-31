import re

# One more thing, in `exportChartDataToCSV` it was:
# `function exportChartDataToCSV(chartInstance, filename) {`
# And in `workbench.html` it was `if(window.volPreExpiryChart) exportChartDataToCSV...`
# Wait, look closely at line 1444:
# `<button class="btn btn-secondary" onclick="if(window.volPreExpiryChart) exportChartDataToCSV(window.volPreExpiryChart, 'Vol_Pre_Expiry'); else exportChartDataToCSV(volPreExpiryChart, 'Vol_Pre_Expiry')">`
# If `exportChartDataToCSV` wasn't globally available, clicking the CSV button would throw an error! But the user said "dead button" and specifically "not a single existing CSV that you provided download anything ... No error".
# If the CSV buttons are dead, `exportChartDataToCSV` might be failing silently or returning early!
# Let's inspect `exportChartDataToCSV` logic!
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()
print(js[js.find('function exportChartDataToCSV'):js.find('function exportChartDataToCSV')+200])
