import re
with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# Fix the incorrect replacements:
html = html.replace("exportTableToCSV('mwpl-analysis-table', 'Rollover_Analysis')", "exportTableToCSV('rollover-analysis-table', 'Rollover_Analysis')")
html = html.replace("exportTableToCSV('mwpl-analysis-table', 'OI_Analysis')", "exportTableToCSV('oi-analysis-table', 'OI_Analysis')")

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(html)
print("Fixed table IDs for Rollover and OI")
