import asyncio
from datetime import date
from backend.ingest.nse_lib import NSELib

lib = NSELib()
d = date(2026, 3, 25)

print("Testing get_mwpl:")
df = lib.get_mwpl(d)
print("MWPL loaded:", not df.empty)

print("Testing get_bhavcopy_fo:")
df2 = lib.get_bhavcopy_fo(d)
print("Bhavcopy FO loaded:", not df2.empty)
