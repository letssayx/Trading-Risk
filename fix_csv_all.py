import re

with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

# I also need to verify that `exportChartDataToCSV` is defined and works for the specific `chartInstance`
print("exportChartDataToCSV defined:", "function exportChartDataToCSV(" in js)

# Let's check `workbench.html` if all the CSV buttons point to the right charts.
with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# Volatility Analysis CSV
print("Vol Pre Expiry CSV:", "exportChartDataToCSV(volPreExpiryChart" in html or "exportChartDataToCSV(window.volPreExpiryChart" in html)
print("Vol Cone CSV:", "exportChartDataToCSV(volConeChart" in html or "exportChartDataToCSV(window.volConeChart" in html)

# Derivatives Analysis Tabs CSV
print("Adv Tech CSV:", "exportChartDataToCSV(echartInstance" in html or "exportChartDataToCSV(window.echartInstance" in html)
print("Market Activity CSV:", "exportChartDataToCSV(fiiDiiChartInstance" in html or "exportChartDataToCSV(window.fiiDiiChartInstance" in html)

# Do we have CSV buttons for ALL charts and tables under derivatives analysis as the user requested?
# "CSV needed in each chart and table in each tab under derivatives analysis"
# Let's list the tabs:
# 1. Data Matrix (deriv-tab-matrix) -> matrix-table
# 2. Basis Watch (deriv-tab-basis) -> basis-table
# 3. Option Chain (deriv-tab-chain) -> opt-chain-table
# 4. Volatility Analysis (deriv-tab-optanalysis) -> vol-pre-expiry-chart, vol-cone-chart
# 5. Option Strategy (deriv-tab-optstrategy) -> opt-strategy-builder
# 6. MWPL Analysis (deriv-tab-mwpl) -> mwpl-table
# 7. OI Analysis (deriv-tab-oi) -> opt-analysis-pcr-chart, opt-analysis-oi-chart
# 8. Rollover Analysis (deriv-tab-rollover) -> rollover-table
# 9. Market Activity (deriv-tab-market) -> fiiDiiChart, participant-oi-daily-summary, and the 6 historical charts
# 10. Adv Technicals (deriv-tab-advtech) -> echart-container
