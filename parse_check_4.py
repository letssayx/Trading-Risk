from datetime import date
from backend.ingest.nse_lib import NSELib
nselib = NSELib()

df = nselib.get_corporate_actions(date(2026, 7, 24))
for i, row in df.iterrows():
    if row['SYMBOL'] == 'RECLTD':
        print(row.to_dict())
