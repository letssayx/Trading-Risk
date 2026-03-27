from datetime import date
from backend.ingest.nse_lib import NSELib

def test_fetch():
    lib = NSELib()
    d = date(2026, 3, 25)

    print("Testing get_mwpl (which uses nsearchives):")
    df1 = lib.get_mwpl(d)
    print("MWPL loaded:", not df1.empty)

    print("\nTesting get_bhavcopy_fo (which uses nsearchives):")
    df2 = lib.get_bhavcopy_fo(d)
    print("Bhavcopy FO loaded:", not df2.empty)

    print("\nTesting get_pe_ratio (which uses nsearchives):")
    df3 = lib.get_pe_ratio(d)
    print("PE Ratio loaded:", not df3.empty)

test_fetch()
