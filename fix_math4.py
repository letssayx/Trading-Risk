import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# I need to move `near_opts` definition UP.
old_vol_skew = """            chg_oi_opts = sum(o.change_in_oi for o in all_opts if o.change_in_oi is not None)
            chg_oi_futs = sum(f.change_in_oi for f in futs if f.change_in_oi is not None)

            # Volatility & Skew
            daily_vol = self._get_daily_vol(target_date, symbol)
            # Proxy annual vol for the root of BS solver (rough approximation using daily_vol * sqrt(365))
            proxy_ann_vol = daily_vol * np.sqrt(365) if daily_vol else 0.20

            near_opts = [o for o in all_opts if o.expiry_date == near_fut.expiry_date]
            next_opts = [o for o in all_opts if next_fut and o.expiry_date == next_fut.expiry_date]
            far_opts = [o for o in all_opts if far_fut and o.expiry_date == far_fut.expiry_date]"""

new_vol_skew = """            chg_oi_opts = sum(o.change_in_oi for o in all_opts if o.change_in_oi is not None)
            chg_oi_futs = sum(f.change_in_oi for f in futs if f.change_in_oi is not None)

            # Volatility & Skew
            daily_vol = self._get_daily_vol(target_date, symbol)
            # Proxy annual vol for the root of BS solver (rough approximation using daily_vol * sqrt(365))
            proxy_ann_vol = daily_vol * np.sqrt(365) if daily_vol else 0.20"""

if old_vol_skew in text:
    text = text.replace(old_vol_skew, new_vol_skew)
else:
    print("Could not find vol skew!")

old_highest_oi = """            valid_opts = [o for o in all_opts if o.expiry_date != target_date]
            if not valid_opts:
                valid_opts = all_opts

            # Highest OI requires the actual specific contract (to get its premium and exact OI)
            # Find the single contract with the highest OI across valid expiries for PE and CE
            highest_pe_contract = None
            highest_ce_contract = None

            # To calculate the highest OI strike properly, we should sum the OI across the near/next expiries per strike
            # or simply find the contract with the absolute highest OI in the entire valid option chain.
            # Usually, traders look at the near-month option chain. Let's filter to near month if possible.
            oi_opts = near_opts if near_opts else valid_opts"""

new_highest_oi = """            valid_opts = [o for o in all_opts if o.expiry_date != target_date]
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
            oi_opts = near_opts if near_opts else valid_opts"""

if old_highest_oi in text:
    text = text.replace(old_highest_oi, new_highest_oi)
    with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
        f.write(text)
    print("Fixed dependencies!")
else:
    print("Could not find highest OI text block.")
