with open("backend/analysis/toolbox/reports/morning_report.py", "r") as f:
    text = f.read()

text = text.replace(
    "record.close_price = self._safe_float(near_fut.close_price)",
    "record.close_price = self._safe_float(near_fut.close_price)\n            record.vwap = self._safe_float(eq_record.avg_price if eq_record and hasattr(eq_record, 'avg_price') else 0.0)"
)

with open("backend/analysis/toolbox/reports/morning_report.py", "w") as f:
    f.write(text)
