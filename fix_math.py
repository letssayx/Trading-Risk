with open("backend/analysis/toolbox/reports/morning_report.py", "r") as f:
    text = f.read()

text = text.replace(
    "record.pct_away_highest_pe = self._safe_float(((highest_pe_strike - cash_close / cash_close * 100 if highest_pe_strike and cash_close else None)))",
    "record.pct_away_highest_pe = self._safe_float(((highest_pe_strike - cash_close) / cash_close) * 100 if highest_pe_strike and cash_close else None)"
)
text = text.replace(
    "record.pct_away_highest_ce = self._safe_float(((highest_ce_strike - cash_close / cash_close * 100 if highest_ce_strike and cash_close else None)))",
    "record.pct_away_highest_ce = self._safe_float(((highest_ce_strike - cash_close) / cash_close) * 100 if highest_ce_strike and cash_close else None)"
)

with open("backend/analysis/toolbox/reports/morning_report.py", "w") as f:
    f.write(text)
