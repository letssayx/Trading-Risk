# Where is `exportTableToCSV` defined?
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

idx = js.find('function exportTableToCSV')
print("Defined at index", idx)
# And `exportChartDataToCSV`?
idx2 = js.find('function exportChartDataToCSV')
print("Defined at index", idx2)

# If BOTH are correctly defined in `script_workbench2.js` and `node -c` passes...
# Is it possible that `exportTableToCSV` throws an error because `table` is not found, so `if (!table) return;` triggers silently?!
# If it returns silently, "No error, its dead button"!
# Let's add an alert inside `if (!table)` so we know if it fails!
js = js.replace('if (!table) return;', 'if (!table) { alert("Table data not loaded yet."); return; }')

with open("backend/ui/static/js/script_workbench2.js", "w") as f:
    f.write(js)
print("Patched exportTableToCSV")
