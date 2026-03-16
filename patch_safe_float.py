with open("backend/analysis/toolbox/reports/morning_report.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_calc = False
inserted_helper = False

for line in lines:
    if "def calculate_for_date" in line and not inserted_helper:
        helper = """    def _safe_float(self, val):
        import numpy as np
        import math
        if val is None: return None
        try:
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        except (ValueError, TypeError):
            return val

"""
        new_lines.append(helper)
        inserted_helper = True
        in_calc = True
        new_lines.append(line)
        continue

    if in_calc and line.strip().startswith("record.") and "=" in line:
        left, right = line.split("=", 1)
        prop = left.strip().split(".")[1]

        # Don't wrap dates or arrays or updated_at
        if prop in ['trade_date', 'symbol', 'near_expiry_date', 'next_expiry_date', 'far_expiry_date', 'mwpl_array', 'updated_at']:
            new_lines.append(line)
        else:
            indent = line[:len(line) - len(line.lstrip())]
            clean_right = right.strip()
            new_lines.append(f"{indent}record.{prop} = self._safe_float({clean_right})\n")
    else:
        new_lines.append(line)

with open("backend/analysis/toolbox/reports/morning_report.py", "w") as f:
    f.writelines(new_lines)
