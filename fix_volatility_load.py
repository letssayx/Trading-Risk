# The html actually DOES have `vol-pre-expiry-chart` and `vol-cone-chart`.
# Why did `print("pre-expiry-chart:", "id=\"vol-pre-expiry-chart\"" in js_code and "id=\"vol-pre-expiry-chart\"" in html)` return False?
# Because I probably had a typo in `js_code`. Let's check `js_code`.
import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js_code = f.read()
print("vol-pre-expiry-chart in js:", "vol-pre-expiry-chart" in js_code)
print("vol-cone-chart in js:", "vol-cone-chart" in js_code)
