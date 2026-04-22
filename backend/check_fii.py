import asyncio
from datetime import date
from ingest.nse_lib import NSELib

async def main():
    lib = NSELib()
    df = lib.get_corporate_actions(date(2025, 3, 4))
    if not df.empty:
        print(df.columns)
        print(df.iloc[0].to_dict())

if __name__ == "__main__":
    asyncio.run(main())
