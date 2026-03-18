import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# Make sure PCR is not inverted. PCR = Put OI / Call OI
# put_oi = sum(o.open_interest for o in all_opts if o.option_type == 'PE')
# call_oi = sum(o.open_interest for o in all_opts if o.option_type == 'CE')
# pcr_oi = (put_oi / call_oi) if call_oi > 0 else 0.0
# This is correct.

# What about % Away PE/CE calculation?
# pct_away_highest_pe = ((highest_pe_strike - cash_close) / cash_close) * 100
# For PE, strike is usually below spot (OTM). So (Strike - Spot) / Spot will be Negative.
# Example Spot = 100, PE Strike = 90. (90 - 100)/100 = -10%. This is logically correct for % away from Spot.
# For CE, strike is usually above spot (OTM). (110 - 100)/100 = +10%. Correct.

# Wait, the user said "Now weekly we need to add ATM straddle, (closest week for Nifty), and ATM monthly Straddle (Near Month), figure out how can this column be added."
# We added this to the table. And we made it calculate for all active F&O symbols if they have weekly options.
