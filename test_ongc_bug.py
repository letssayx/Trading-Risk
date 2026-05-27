from datetime import datetime, timedelta, date

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
    bms.sort(key=lambda x: x.meeting_date or x.broadcast_date or x.date or datetime.date.min, reverse=True)

    deduplicated_bms = []
    for bm in bms:
        is_duplicate = False
        bm_date = bm.meeting_date or bm.broadcast_date or bm.date
        if hasattr(bm_date, 'date'):
            bm_date = bm_date.date()

        for existing in deduplicated_bms:
            existing_date = existing.meeting_date or existing.broadcast_date or existing.date
            if hasattr(existing_date, 'date'):
                existing_date = existing_date.date()

            if bm_date and existing_date:
                diff_days = abs((bm_date - existing_date).days)
                if diff_days <= 60 and bm.extracted_dividend_type == existing.extracted_dividend_type:
                    is_duplicate = True
                    if not existing.extracted_dividend_amount and bm.extracted_dividend_amount:
                        existing.extracted_dividend_amount = bm.extracted_dividend_amount
                    break

        if not is_duplicate:
            deduplicated_bms.append(bm)

    return deduplicated_bms

# Example data representing the ONGC bug: multiple board meetings for same dividend cycle
bms = [
    DummyBM(datetime(2026, 5, 26), "Final", 1.0, "Board Meeting Intimation/Dividend"),
    DummyBM(datetime(2026, 5, 26), "Final", 1.0, "Financial Results/Dividend/Other business matters"),
    DummyBM(datetime(2026, 5, 15), "Final", None, "Board Meeting Intimation (rescheduled)")
]

deduplicated = run_dedup(bms)
for d in deduplicated:
    print(f"BM: date={d.meeting_date}, amount={d.extracted_dividend_amount}, type={d.extracted_dividend_type}, purpose={d.purpose}")
