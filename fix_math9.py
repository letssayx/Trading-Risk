import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# Fix percentage away for PE/CE as well. They use cash_close, but what if cash_close is 0?
pct_away1 = """record.pct_away_highest_pe = self._safe_float(((highest_pe_strike - cash_close) / cash_close) * 100 if highest_pe_strike and cash_close else None)"""
pct_away1_fixed = """record.pct_away_highest_pe = self._safe_float(((highest_pe_strike - ref_price) / ref_price) * 100 if highest_pe_strike and ref_price else None)"""

pct_away2 = """record.pct_away_highest_ce = self._safe_float(((highest_ce_strike - cash_close) / cash_close) * 100 if highest_ce_strike and cash_close else None)"""
pct_away2_fixed = """record.pct_away_highest_ce = self._safe_float(((highest_ce_strike - ref_price) / ref_price) * 100 if highest_ce_strike and ref_price else None)"""

if pct_away1 in text:
    text = text.replace(pct_away1, pct_away1_fixed)
if pct_away2 in text:
    text = text.replace(pct_away2, pct_away2_fixed)

with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
    f.write(text)
print("Done pct away")
