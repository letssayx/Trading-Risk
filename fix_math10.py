import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# Update `calculate_iv_and_skew` calls to use `ref_price` instead of `cash_close`!
# Otherwise IV for indices like NIFTY will use 0.0 for spot price, returning NaN.

iv_1 = """atm_iv_near, skew_near = self.calculate_iv_and_skew(near_opts, cash_close, near_fut.expiry_date, target_date, proxy_ann_vol)"""
iv_2 = """atm_iv_next, _ = self.calculate_iv_and_skew(next_opts, cash_close, next_fut.expiry_date, target_date, proxy_ann_vol) if next_fut else (0.0, 0.0)"""
iv_3 = """_, skew_far = self.calculate_iv_and_skew(far_opts, cash_close, far_fut.expiry_date, target_date, proxy_ann_vol) if far_fut else (0.0, 0.0)"""

text = text.replace(iv_1, """atm_iv_near, skew_near = self.calculate_iv_and_skew(near_opts, ref_price, near_fut.expiry_date, target_date, proxy_ann_vol)""")
text = text.replace(iv_2, """atm_iv_next, _ = self.calculate_iv_and_skew(next_opts, ref_price, next_fut.expiry_date, target_date, proxy_ann_vol) if next_fut else (0.0, 0.0)""")
text = text.replace(iv_3, """_, skew_far = self.calculate_iv_and_skew(far_opts, ref_price, far_fut.expiry_date, target_date, proxy_ann_vol) if far_fut else (0.0, 0.0)""")

with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
    f.write(text)
print("Done IV reference price update.")
