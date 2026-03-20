import asyncio
from datetime import date
from ingest.nse_lib import NSELib

def main():
    lib = NSELib()
    # The image shows HDFCBANK broadcast was 18-Mar-2025, meeting is 19-Apr-2025
    df = lib.get_board_meetings(date(2025, 3, 18))
    if df is not None and not df.empty:
        hdfc = df[df['SYMBOL'] == 'HDFCBANK']
        if not hdfc.empty:
            print("HDFCBANK data:")
            print(hdfc.iloc[0].to_dict())
        else:
            print("HDFC not found in 18-Mar-2025, showing first row dict:")
            print(df.iloc[0].to_dict())
    else:
        print("No data found or request failed.")

if __name__ == "__main__":
    main()
