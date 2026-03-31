# If the load volatility button "feels dead", maybe there's an error happening right away.
# Or maybe `exportChartDataToCSV` is failing?
# Let's inspect `exportChartDataToCSV` implementation which I just added in a previous submission.
# The user said "existing CSV that you provided download anything ... No error, its dead button".
# If `exportChartDataToCSV` has a syntax error, the whole file might fail to load! Or it's just broken.
# Let's check `backend/ui/static/js/script_workbench2.js` for `exportChartDataToCSV`.

import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

if "exportChartDataToCSV" in js:
    print("exportChartDataToCSV found")
else:
    print("exportChartDataToCSV NOT found!")
