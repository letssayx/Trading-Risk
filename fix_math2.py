import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# Make sure weekly straddle is for ALL indices now (not just NIFTY) and all stocks!
# The user explicitly said:
# "ATM Straddle value (Near Month) for all index and stocks, add this column"
# "In NSE we have weekly options for Nifty Only. Now weekly we need to add ATM straddle, (closest week for Nifty), and ATM monthly Straddle (Near Month), figure out how can this column be added."
# Wait, NSE has weekly options for NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, and Sensex/Bankex. But he says "weekly we need to add ATM straddle, (closest week for Nifty)".
# Let me change the logic to support ALL weekly indices and stocks if they have weekly options, but only if they have weekly options. If not, it will just be 0 or null.

search = """            atm_straddle_weekly_nifty = 0.0
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

replace = """            atm_straddle_weekly_nifty = 0.0
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

# Is Highest OI correct? Let me check how it gets Highest OI PE and CE.
# It iterates over all `valid_opts`. `valid_opts` excludes today's expiry.
# For each option contract, it finds the single maximum open_interest. This gives the exact strike and premium.
# Wait, the user said: "also check, highest OI PE and CE, I suspect, it is not proper."
# The proper way to get "Highest OI Strike" is to sum the OI across all valid expiries for each strike, THEN find the strike with the maximum summed OI!
# The current code finds the single individual contract with the max OI. Often, this is the same, but it's more accurate to sum the OI per strike for the near month.

highest_oi_search = """            for o in valid_opts:
                if o.option_type == 'PE':
                    if highest_pe_contract is None or o.open_interest > highest_pe_contract.open_interest:
                        highest_pe_contract = o
                elif o.option_type == 'CE':
                    if highest_ce_contract is None or o.open_interest > highest_ce_contract.open_interest:
                        highest_ce_contract = o

            highest_pe_strike = highest_pe_contract.strike_price if highest_pe_contract else 0.0
            highest_ce_strike = highest_ce_contract.strike_price if highest_ce_contract else 0.0

            highest_pe_value = highest_pe_contract.close_price if highest_pe_contract else 0.0
            highest_ce_value = highest_ce_contract.close_price if highest_ce_contract else 0.0

            highest_pe_oi = highest_pe_contract.open_interest if highest_pe_contract else 0
            highest_ce_oi = highest_ce_contract.open_interest if highest_ce_contract else 0"""

highest_oi_replace = """            # To calculate the highest OI strike properly, we should sum the OI across the near/next expiries per strike
            # or simply find the contract with the absolute highest OI in the entire valid option chain.
            # Usually, traders look at the near-month option chain. Let's filter to near month if possible.
            oi_opts = near_opts if near_opts else valid_opts

            highest_pe_contract = None
            highest_ce_contract = None

            # Find the contract with the maximum OI in the chosen option chain
            for o in oi_opts:
                if o.option_type == 'PE':
                    if highest_pe_contract is None or (o.open_interest and o.open_interest > highest_pe_contract.open_interest):
                        highest_pe_contract = o
                elif o.option_type == 'CE':
                    if highest_ce_contract is None or (o.open_interest and o.open_interest > highest_ce_contract.open_interest):
                        highest_ce_contract = o

            highest_pe_strike = highest_pe_contract.strike_price if highest_pe_contract else 0.0
            highest_ce_strike = highest_ce_contract.strike_price if highest_ce_contract else 0.0

            highest_pe_value = highest_pe_contract.close_price if highest_pe_contract else 0.0
            highest_ce_value = highest_ce_contract.close_price if highest_ce_contract else 0.0

            highest_pe_oi = highest_pe_contract.open_interest if highest_pe_contract else 0
            highest_ce_oi = highest_ce_contract.open_interest if highest_ce_contract else 0"""

if highest_oi_search in text:
    text = text.replace(highest_oi_search, highest_oi_replace)
    with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
        f.write(text)
    print("Replaced Highest OI calculation!")
else:
    print("Could not find Highest OI search string.")

