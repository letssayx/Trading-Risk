import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# Make sure rollover is not * 100 twice!
# In script_workbench2.js:
# const roll = (row.rollover_pct != null && !isNaN(Number(row.rollover_pct))) ? (Number(row.rollover_pct) * 100).toFixed(2) + '%' : '-';
# IF backend computes: rollover_pct = (sum(...) / total_oi * 100), then JS multiplying by 100 will make it 10,000%!
# Let's fix this so backend stores it as a true decimal (e.g. 0.85 for 85%).
old_roll = """rollover_pct = (sum(f.open_interest for f in futs[1:]) / total_oi * 100) if total_oi > 0 else 0.0"""
new_roll = """rollover_pct = (sum(f.open_interest for f in futs[1:]) / total_oi) if total_oi > 0 else 0.0"""

if old_roll in text:
    text = text.replace(old_roll, new_roll)
    with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
        f.write(text)
    print("Fixed rollover_pct decimal issue.")
else:
    print("Could not find rollover_pct")
