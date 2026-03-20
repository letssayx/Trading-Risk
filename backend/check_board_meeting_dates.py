import asyncio
from datetime import date
from ingest.nse_lib import NSELib
import pandas as pd

async def main():
    lib = NSELib()
    df = lib.get_board_meetings(date(2025, 3, 11))
    if not df.empty:
        print(df[['SYMBOL', 'MEETING DATE', 'bm_timestamp', 'sysTime']].head())

if __name__ == "__main__":
    asyncio.run(main())
