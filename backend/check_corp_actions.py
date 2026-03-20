import asyncio
from datetime import date
from ingest.nse_lib import NSELib
import pandas as pd

async def main():
    lib = NSELib()
    df = lib.get_corporate_actions(date(2025, 3, 18))
    if not df.empty:
        # Just print one full row to see contents clearly
        print(df.iloc[0].to_dict())

if __name__ == "__main__":
    asyncio.run(main())
