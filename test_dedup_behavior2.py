import sys
sys.path.append('.')
from backend.ingest.nse_importer import NSEDataImporter

importer = NSEDataImporter()
records = [
    {'date': '2026-05-05', 'symbol': 'LT', 'purpose': 'Board Meeting Intimation', 'extracted_dividend_amount': 38},
    {'date': '2026-05-05', 'symbol': 'LT', 'purpose': 'Financial Results/Dividend', 'extracted_dividend_amount': 38}
]
unique_fields = ['date', 'symbol', 'purpose']

deduped = importer._deduplicate_records(records, unique_fields)
print("Deduped length:", len(deduped))
for r in deduped:
    print(r)
