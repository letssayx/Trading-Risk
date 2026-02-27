
import pandas as pd
import sys
import os
from datetime import date

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ingest.field_mapper import FieldMapper

def test_mwpl_parsing_reproduction():
    print("Testing MWPL parsing with merged header reproduction...")

    # Data from user screenshot
    data = [
        ["Sr No.", "Underlying Stock", "Client 1", "Client 2", "Client 3"],
        ["1", "ABCAPITAL", "7.97", "7.79", "6.99"],
        ["2", "ADANIENSOL", "7.00", "5.01", "4.51"]
    ]

    # Simulate read_excel default behavior: header=0 (first row is header)
    # The first row is "Position as percentage (%) of MWPL", followed by NaNs for merged cells
    columns = ["Position as percentage (%) of MWPL", "Unnamed: 1", "Unnamed: 2", "Unnamed: 3", "Unnamed: 4"]

    df = pd.DataFrame(data, columns=columns)

    print("DataFrame Head:")
    print(df.head())
    print("\nColumns:", df.columns.tolist())

    # 1. Test Detection
    print("\n--- Detection Phase ---")
    detected = FieldMapper.detect_format(df)
    print(f"Detected Format: {detected}")

    # If detection fails (returns unknown), we stop
    if detected['type'] == 'unknown':
        print("FAILURE: Format not detected correctly (expected 'mwpl').")
    else:
        print("SUCCESS: Format detected correctly.")

    # 2. Test Mapping
    print("\n--- Mapping Phase ---")
    try:
        records = FieldMapper.map_to_records(df, detected, trade_date=date(2026, 2, 5))
        print(f"Mapped Records: {len(records)}")
        for r in records[:2]:
            print(r)

        if len(records) == 0:
             print("FAILURE: No records mapped. Header row probably not found.")
        elif records[0]['underlying_stock'] == 'ABCAPITAL':
             print("SUCCESS: Records mapped correctly.")
        else:
             print(f"FAILURE: Unexpected first record: {records[0]}")

    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_mwpl_parsing_reproduction()
