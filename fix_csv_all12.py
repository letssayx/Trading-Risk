# Wait, `html[html.find('deriv-tab-rollover'):]` will just find the NEXT table in the whole file if there isn't one in the tab!
# `mwpl-analysis-table` was found because it's AFTER `deriv-tab-rollover` in the DOM tree if rollover has no table in HTML.
# Let's check `rolloverTool.js` to see what table it creates!
import re
with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    rjs = f.read()

match = re.search(r'<table[^>]*id="([^"]+)"', rjs)
if match:
    print("Rollover Tool Table ID:", match.group(1))

with open("backend/ui/static/js/oiTool.js", "r") as f:
    ojs = f.read()

match = re.search(r'<table[^>]*id="([^"]+)"', ojs)
if match:
    print("OI Tool Table ID:", match.group(1))
