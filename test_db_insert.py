from datetime import date
from backend.ingest.nse_models import CorporateAction

try:
    c = CorporateAction(date=date(2026,3,20), symbol='TEST', parsed_dividend_amount=10.0, dividend_type='Final')
    print("CorporateAction created:", c)
except Exception as e:
    print("Error:", e)
