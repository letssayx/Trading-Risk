import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

search = """record.delivery_pct = self._safe_float(mto_record.delivery_to_traded_pct if mto_record else 0.0)"""
replace = """record.delivery_pct = self._safe_float(mto_record.deliverable_pct if mto_record else 0.0)"""

if search in text:
    text = text.replace(search, replace)
    with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
        f.write(text)
    print("Fixed MTODelivery attribute error.")
else:
    print("Could not find search block.")
