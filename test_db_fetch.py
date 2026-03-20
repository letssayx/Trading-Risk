import asyncio
from datetime import date
from backend.ingest.nse_lib import NSELib

client = NSELib()
df = client.get_corporate_actions(date(2025, 1, 1))
if not df.empty:
     print("CA Columns:", df.columns.tolist())
     print(df.head(1).to_dict('records'))
else:
     print("CA Empty")

df2 = client.get_board_meetings(date(2025, 1, 1))
if not df2.empty:
     print("BM Columns:", df2.columns.tolist())
     print(df2.head(1).to_dict('records'))
else:
     print("BM Empty")
