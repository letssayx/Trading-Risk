import sys
import datetime
sys.path.append('.')
from backend.ingest.nse_lib import NSELib
import asyncio

async def test():
    lib = NSELib()
    date_to_test = datetime.date(2026, 4, 27)
    df = lib.get_board_meetings(date_to_test)
    if not df.empty:
        # Filter for coalindia
        df_c = df[df['SYMBOL'] == 'COALINDIA']
        print(df_c)

    print("\n--- CA ---")
    df_ca = lib.get_corporate_actions(date_to_test)
    if not df_ca.empty:
        df_ca_c = df_ca[df_ca['SYMBOL'] == 'COALINDIA']
        print(df_ca_c)

asyncio.run(test())
