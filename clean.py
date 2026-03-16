import re

with open("backend/analysis/toolbox/reports/morning_report.py", "r") as f:
    text = f.read()

# remove all self._safe_float( ) layers
for _ in range(10):
    text = re.sub(r'self\._safe_float\((.*?)\)', r'\1', text)

with open("backend/analysis/toolbox/reports/morning_report.py", "w") as f:
    f.write(text)
