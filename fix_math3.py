import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# I need to fix `oi_opts = near_opts if near_opts else valid_opts`.
# BUT `near_opts` is defined AFTER this code!
