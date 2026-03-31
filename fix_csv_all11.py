# Ah! `mwpl-table` doesn't exist, but `mwpl-analysis-table` DOES!
# `rollover-table` doesn't exist?
# Let's search the HTML for table IDs.
import re
with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# I added `exportTableToCSV('mwpl-table', 'MWPL_Analysis')` but the actual table is `mwpl-analysis-table`.
html = html.replace("exportTableToCSV('mwpl-table',", "exportTableToCSV('mwpl-analysis-table',")

# What about rollover?
match = re.search(r'<table[^>]*id="([^"]+)"', html[html.find('deriv-tab-rollover'):])
if match:
    print("Rollover Table ID:", match.group(1))
    html = html.replace("exportTableToCSV('rollover-table',", f"exportTableToCSV('{match.group(1)}',")

# What about oi-tool?
match = re.search(r'<table[^>]*id="([^"]+)"', html[html.find('deriv-tab-oi'):])
if match:
    print("OI Table ID:", match.group(1))
    html = html.replace("exportTableToCSV('oi-tool-table',", f"exportTableToCSV('{match.group(1)}',")
else:
    # Maybe OI tool table is generated dynamically inside `oi-tool-container`?
    # Let's check `oiTool.js`!
    pass

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(html)
