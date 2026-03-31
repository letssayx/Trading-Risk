from datetime import date
from backend.ingest.nse_lib import NSELib
import logging

logging.basicConfig(level=logging.INFO)

lib = NSELib()
df = lib.get_contract_delta(date(2025, 3, 28)) # Try a recent Friday
if not df.empty:
    print(f"Success! Fetched {len(df)} rows.")
else:
    print("Failed to fetch.")
