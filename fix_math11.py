import re

with open('backend/analysis/toolbox/reports/morning_report.py', 'r') as f:
    text = f.read()

# I need to add total_eq_volume and delivery_pct to the record saving block!
search = """            record.eq_close_price = self._safe_float(cash_close)
            record.vwap = self._safe_float(eq_record.avg_price if eq_record and hasattr(eq_record, 'avg_price') else 0.0)
            record.futures_total_vol = self._safe_float(total_vol)"""

replace = """            record.eq_close_price = self._safe_float(cash_close)
            record.vwap = self._safe_float(eq_record.avg_price if eq_record and hasattr(eq_record, 'avg_price') else 0.0)
            record.total_eq_volume = self._safe_float(eq_record.total_traded_qty if eq_record and hasattr(eq_record, 'total_traded_qty') else 0)

            # Fetch delivery percentage for the day
            mto_record = self.db.query(MTODelivery).filter(
                MTODelivery.trade_date == target_date,
                MTODelivery.security_name.in_([symbol, getattr(eq_record, 'series', '')])
            ).first()
            record.delivery_pct = self._safe_float(mto_record.delivery_to_traded_pct if mto_record else 0.0)

            record.futures_total_vol = self._safe_float(total_vol)"""

if search in text:
    text = text.replace(search, replace)
    with open('backend/analysis/toolbox/reports/morning_report.py', 'w') as f:
        f.write(text)
    print("Added total_eq_volume and delivery_pct to math engine!")
else:
    print("Could not find search block.")
