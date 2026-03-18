import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# Make sure near_fut.close_price is actually used if cash_close = 0 for the straddles.
# Indices without historical index data may have 0 cash_close!
# The straddle calculation uses `cash_close > 0`. We should fall back to `near_fut.close_price`!

straddle_logic = """            atm_straddle_near_month = 0.0
            straddle_near_opts = near_opts
            if near_fut and near_fut.expiry_date == target_date and next_opts:
                straddle_near_opts = next_opts

            if straddle_near_opts and cash_close > 0:"""

straddle_logic_fixed = """            atm_straddle_near_month = 0.0
            straddle_near_opts = near_opts
            if near_fut and near_fut.expiry_date == target_date and next_opts:
                straddle_near_opts = next_opts

            ref_price = cash_close if cash_close > 0 else (near_fut.close_price if near_fut else 0.0)

            if straddle_near_opts and ref_price > 0:"""

if straddle_logic in text:
    text = text.replace(straddle_logic, straddle_logic_fixed)
else:
    print("Not found 1")

weekly_logic = """            atm_straddle_weekly_nifty = 0.0
            if cash_close > 0:"""

weekly_logic_fixed = """            atm_straddle_weekly_nifty = 0.0
            if ref_price > 0:"""

if weekly_logic in text:
    text = text.replace(weekly_logic, weekly_logic_fixed)
else:
    print("Not found 2")

text = text.replace('abs(x - cash_close)', 'abs(x - ref_price)')

with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
    f.write(text)

print("Fixed straddle reference prices")
