import re

with open("backend/analysis/toolbox/reports/morning_report.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_calc_for_date = False
for line in lines:
    if "def calculate_for_date" in line:
        in_calc_for_date = True

    if in_calc_for_date and "record." in line and "=" in line:
        # Match something like `record.atm_iv_near = atm_iv_near`
        m = re.match(r'^(\s+record\.\w+\s*=\s*)(.+)$', line)
        if m:
            prefix = m.group(1)
            val = m.group(2)
            # Skip if it's already a method call or simple None
            if val.strip() == "None":
                new_lines.append(line)
            else:
                new_lines.append(f"{prefix}self._safe_float({val})\n")
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open("backend/analysis/toolbox/reports/morning_report.py", "w") as f:
    f.writelines(new_lines)
