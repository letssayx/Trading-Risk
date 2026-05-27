import datetime
from datetime import date

class DummyBM:
    def __init__(self, meeting_date, extracted_dividend_type, extracted_dividend_amount, purpose, broadcast_date=None, date_obj=None):
        self.meeting_date = meeting_date
        self.extracted_dividend_type = extracted_dividend_type
        self.extracted_dividend_amount = extracted_dividend_amount
        self.purpose = purpose
        self.broadcast_date = broadcast_date
        self.date = date_obj

def run_dedup(bms):
    today = date.today()

    def safe_date_sort(x):
        d = x.meeting_date or x.broadcast_date or x.date
        if d is None:
            return datetime.date.min
        if hasattr(d, 'date'):
            return d.date()
        return d

    bms.sort(key=safe_date_sort, reverse=True)

    deduplicated_bms = []
    for bm in bms:
        is_duplicate = False
        bm_date = safe_date_sort(bm)

        for existing in deduplicated_bms:
            existing_date = existing['sort_date']

            if bm_date and existing_date and bm_date != datetime.date.min and existing_date != datetime.date.min:
                diff_days = abs((bm_date - existing_date).days)
                # Merge synthetics if they are within 60 days of each other and have the same dividend type
                if diff_days <= 60 and bm.extracted_dividend_type == existing['bm'].extracted_dividend_type:
                    is_duplicate = True
                    # Update amount if the newer duplicate has it
                    if not existing['extracted_dividend_amount'] and bm.extracted_dividend_amount:
                        existing['extracted_dividend_amount'] = bm.extracted_dividend_amount
                    break

        if not is_duplicate:
            deduplicated_bms.append({
                'bm': bm,
                'sort_date': bm_date,
                'extracted_dividend_amount': bm.extracted_dividend_amount
            })

    return deduplicated_bms

# Mix of date and datetime to test sorting crash fix
bms = [
    DummyBM(datetime.datetime(2026, 5, 26), "Final", 1.0, "Board Meeting Intimation/Dividend"),
    DummyBM(datetime.date(2026, 5, 26), "Final", 1.0, "Financial Results/Dividend/Other business matters"),
    DummyBM(datetime.datetime(2026, 5, 15), "Final", None, "Board Meeting Intimation (rescheduled)")
]

deduplicated = run_dedup(bms)
for d in deduplicated:
    print(f"BM: date={d['bm'].meeting_date}, amount={d['extracted_dividend_amount']}, type={d['bm'].extracted_dividend_type}")
