import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# Make weekly straddle calculation work for ALL symbols (so if BANKNIFTY has weekly options, it computes it too).
old_weekly = """            atm_straddle_weekly_nifty = 0.0
            if symbol == 'NIFTY' and cash_close > 0:
                # Find all active expiries for NIFTY options strictly after today if today is an expiry
                nifty_expiries = list(set([o.expiry_date for o in all_opts if o.expiry_date >= target_date]))
                nifty_expiries.sort()

                # If today is the closest expiry, use the next one (next week)
                if nifty_expiries and nifty_expiries[0] == target_date and len(nifty_expiries) > 1:
                    closest_weekly_expiry = nifty_expiries[1]
                elif nifty_expiries:
                    closest_weekly_expiry = nifty_expiries[0]
                else:
                    closest_weekly_expiry = None

                if closest_weekly_expiry:
                    weekly_opts = [o for o in all_opts if o.expiry_date == closest_weekly_expiry]
                    if weekly_opts:
                        weekly_strikes = list(set([o.strike_price for o in weekly_opts]))
                        if weekly_strikes:
                            weekly_atm_strike = min(weekly_strikes, key=lambda x: abs(x - cash_close))
                            w_ce_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type == 'CE'), 0.0)
                            w_pe_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type == 'PE'), 0.0)
                            atm_straddle_weekly_nifty = w_ce_price + w_pe_price"""

new_weekly = """            atm_straddle_weekly_nifty = 0.0
            if cash_close > 0:
                # Find all active expiries for options strictly after today if today is an expiry
                sym_expiries = list(set([o.expiry_date for o in all_opts if o.expiry_date >= target_date]))
                sym_expiries.sort()

                # If today is the closest expiry, use the next one (next week)
                if sym_expiries and sym_expiries[0] == target_date and len(sym_expiries) > 1:
                    closest_weekly_expiry = sym_expiries[1]
                elif sym_expiries:
                    closest_weekly_expiry = sym_expiries[0]
                else:
                    closest_weekly_expiry = None

                if closest_weekly_expiry:
                    weekly_opts = [o for o in all_opts if o.expiry_date == closest_weekly_expiry]
                    if weekly_opts:
                        weekly_strikes = list(set([o.strike_price for o in weekly_opts]))
                        if weekly_strikes:
                            weekly_atm_strike = min(weekly_strikes, key=lambda x: abs(x - cash_close))
                            w_ce_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type == 'CE'), 0.0)
                            w_pe_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type == 'PE'), 0.0)
                            atm_straddle_weekly_nifty = w_ce_price + w_pe_price"""

if old_weekly in text:
    text = text.replace(old_weekly, new_weekly)
    with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
        f.write(text)
    print("Fixed weekly straddle.")
else:
    print("Could not find weekly straddle.")
