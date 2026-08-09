from datetime import date, datetime
from backend.ingest.nse_lib import NSELib
import json

nselib = NSELib()

# Test COALINDIA dates
d = date(2026, 7, 24)
bm_df = nselib.get_board_meetings(d)
if not bm_df.empty:
    print("BM Data:", bm_df[bm_df['SYMBOL'] == 'COALINDIA'].to_dict('records'))
    print("BM Data RECLTD:", bm_df[bm_df['SYMBOL'] == 'RECLTD'].to_dict('records'))

ca_df = nselib.get_corporate_actions(d)
if not ca_df.empty:
    print("CA Data:", ca_df[ca_df['SYMBOL'] == 'COALINDIA'].to_dict('records'))
    print("CA Data RECLTD:", ca_df[ca_df['SYMBOL'] == 'RECLTD'].to_dict('records'))
