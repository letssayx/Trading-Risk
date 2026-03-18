import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# We need to change the logic to sum OI by strike across valid options (excluding today's expiry).
# For premium, we will use the near month premium of that strike.

old_highest_oi = """            valid_opts = [o for o in all_opts if o.expiry_date != target_date]
            if not valid_opts:
                valid_opts = all_opts

            near_opts = [o for o in all_opts if near_fut and o.expiry_date == near_fut.expiry_date]
            next_opts = [o for o in all_opts if next_fut and o.expiry_date == next_fut.expiry_date]
            far_opts = [o for o in all_opts if far_fut and o.expiry_date == far_fut.expiry_date]

            # Highest OI requires the actual specific contract (to get its premium and exact OI)
            # Find the single contract with the highest OI across valid expiries for PE and CE
            highest_pe_contract = None
            highest_ce_contract = None

            # To calculate the highest OI strike properly, we should sum the OI across the near/next expiries per strike
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

new_highest_oi = """            valid_opts = [o for o in all_opts if o.expiry_date != target_date]
            if not valid_opts:
                valid_opts = all_opts

            near_opts = [o for o in all_opts if near_fut and o.expiry_date == near_fut.expiry_date]
            next_opts = [o for o in all_opts if next_fut and o.expiry_date == next_fut.expiry_date]
            far_opts = [o for o in all_opts if far_fut and o.expiry_date == far_fut.expiry_date]

            # Highest OI: Sum open_interest by strike across all valid options (excluding today's expiry).
            # The true picture of support/resistance is the summation of OI across all active series for a strike.

            pe_strike_oi_map = {}
            ce_strike_oi_map = {}

            for o in valid_opts:
                if o.open_interest is not None:
                    if o.option_type == 'PE':
                        pe_strike_oi_map[o.strike_price] = pe_strike_oi_map.get(o.strike_price, 0) + o.open_interest
                    elif o.option_type == 'CE':
                        ce_strike_oi_map[o.strike_price] = ce_strike_oi_map.get(o.strike_price, 0) + o.open_interest

            highest_pe_strike = max(pe_strike_oi_map, key=pe_strike_oi_map.get) if pe_strike_oi_map else 0.0
            highest_ce_strike = max(ce_strike_oi_map, key=ce_strike_oi_map.get) if ce_strike_oi_map else 0.0

            highest_pe_oi = pe_strike_oi_map.get(highest_pe_strike, 0)
            highest_ce_oi = ce_strike_oi_map.get(highest_ce_strike, 0)

            # For premium (Highest OI Value), we look at the near month premium for that strike.
            highest_pe_value = next((o.close_price for o in near_opts if o.strike_price == highest_pe_strike and o.option_type == 'PE'), 0.0)
            highest_ce_value = next((o.close_price for o in near_opts if o.strike_price == highest_ce_strike and o.option_type == 'CE'), 0.0)"""

if old_highest_oi in text:
    text = text.replace(old_highest_oi, new_highest_oi)
    with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
        f.write(text)
    print("Replaced highest OI logic")
else:
    print("Could not find highest OI logic block!")
