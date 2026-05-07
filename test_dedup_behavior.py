import sys
sys.path.append('.')
from backend.ingest.nse_importer import NSEImporter

class DummyModel:
    pass

importer = NSEImporter()
records = [
    {'date': '2026-05-05', 'symbol': 'LT', 'purpose': 'Board Meeting Intimation', 'extracted_dividend_amount': 38},
    {'date': '2026-05-05', 'symbol': 'LT', 'purpose': 'Financial Results/Dividend', 'extracted_dividend_amount': 38}
]
unique_fields = ['date', 'symbol', 'purpose']

deduped = importer._deduplicate_records(records, unique_fields)
print("Deduped:", deduped)

# Ah! The problem is that the "purpose" field is different across these two announcements!
# One is "Board Meeting Intimation" and the other is "Financial Results/Dividend".
# So they are NOT considered duplicates by `_deduplicate_records`!
