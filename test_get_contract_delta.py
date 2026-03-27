from datetime import date
from backend.ingest.nse_lib import NSELib
import logging

logging.basicConfig(level=logging.INFO)
lib = NSELib()
df = lib.get_contract_delta(date(2026, 3, 26))
print("Empty:", df.empty)
