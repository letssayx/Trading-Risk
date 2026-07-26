from datetime import date
from backend.ingest.nse_lib import NSELib
import json

nselib = NSELib()
d = date(2026, 7, 24)
bm_df = nselib.get_board_meetings(d)
for i, row in bm_df.iterrows():
    if row['SYMBOL'] in ('COALINDIA', 'RECLTD'):
        print(row['SYMBOL'], row['MEETING DATE'], row['EXTRACTED_DIVIDEND_AMOUNT'], row['EXTRACTED_DIVIDEND_TYPE'], row['EXTRACTED_RECORD_DATE'])
