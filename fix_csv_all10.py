# If it's `tableId`, I should double check all table IDs passed.
with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

import re
# Find all exportTableToCSV
tables = re.findall(r"exportTableToCSV\('([^']+)'", html)
print("Tables to export:", set(tables))

# Check if these IDs actually exist in the HTML!
for table in set(tables):
    if f'id="{table}"' in html:
        print(f"Table {table} EXISTS")
    else:
        print(f"Table {table} MISSING!")

# For charts
charts = re.findall(r"exportChartDataToCSV\('([^']+)'", html)
# Actually, I pass the window object for charts, not the ID.
# `exportChartDataToCSV(echartInstance, '...')`
