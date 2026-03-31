# The user said "not a single existing CSV that you provided download anything ... No error, its dead button".
# I just fixed `script_workbench2.js` syntax error which killed everything.
# Let's ensure `exportTableToCSV` is defined in `script_workbench2.js`
import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

print("exportTableToCSV defined:", "function exportTableToCSV" in js)
