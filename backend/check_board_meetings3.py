from datetime import date
from ingest.nse_lib import NSELib

def main():
    lib = NSELib()
    # Let's try 18-Mar-2025 as the date for 'get_board_meetings' again but look for HDFCBANK or print all symbols
    df = lib.get_board_meetings(date(2025, 3, 18))
    print(df['SYMBOL'].tolist() if not df.empty else "Empty")
    # Actually wait! The NSE json returns the meetings *happening* on that date usually. Or the ones *announced* on that date.
    # The image says HDFCBANK meeting is on 19-Apr-2025, broadcast is 18-Mar-2025.
    # If the user's `trade_date` argument maps to `MEETING DATE`, let's try 19-Apr-2025
    df2 = lib.get_board_meetings(date(2025, 4, 19))
    if not df2.empty:
        hdfc = df2[df2['SYMBOL'] == 'HDFCBANK']
        if not hdfc.empty:
            print("\nHDFCBANK data for 19-Apr-2025:")
            print(hdfc.iloc[0].to_dict())

if __name__ == "__main__":
    main()
