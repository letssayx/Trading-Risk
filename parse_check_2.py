from datetime import date
from backend.ingest.nse_lib import NSELib
import json
import logging

logging.basicConfig(level=logging.DEBUG)

nselib = NSELib()
d = date(2026, 7, 24)

# Let's directly parse the CA and see why the EX-DATE wasn't synthesized for RECLTD.
df = nselib.get_corporate_actions(d)
for i, row in df.iterrows():
    if row['SYMBOL'] in ('COALINDIA', 'RECLTD'):
        print("CA: ", row.to_dict())
