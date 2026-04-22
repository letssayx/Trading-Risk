import asyncio
from datetime import date, timedelta
from ingest.nse_lib import NSELib

async def main():
    lib = NSELib()
    for i in range(10):
        df = lib.get_corporate_actions(date(2025, 3, 1) + timedelta(days=i))
        if not df.empty and 'caBroadcastDate' in df.columns:
            valid = df.dropna(subset=['caBroadcastDate'])
            if not valid.empty:
                print(valid[['SYMBOL', 'caBroadcastDate', 'EX-DATE', 'PURPOSE']].head())
                return
    print("No non-null caBroadcastDate found.")

if __name__ == "__main__":
    asyncio.run(main())
