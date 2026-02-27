"""
Verification script for MWPL robust parsing logic.
This script mocks the NSELib behavior with a simulated "dirty" MWPL file
and verifies that FieldMapper correctly extracts the data.
"""
import sys
import os
import pandas as pd
import logging
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from backend.ingest.field_mapper import FieldMapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_mwpl_df():
    """Create a DataFrame simulating a 'dirty' MWPL file."""
    # Simulate a file with garbage header rows
    data = [
        ["National Stock Exchange of India Ltd.", "", "", "", ""],
        ["Market Wide Position Limit", "", "", "", ""],
        ["Report Date: 05-02-2026", "", "", "", ""],
        ["", "", "", "", ""],  # Empty row
        # The actual header row (often variable)
        ["Symbol", "Underlying Stock", "Client 1", "Client 2", "Client 3"],
        # Data rows
        ["", "RELIANCE", "500000", "200000", "10000"],
        ["", "TCS", "300000", "150000", "5000"],
        ["", "INFY", "400000", "100000", "2000"]
    ]
    df = pd.DataFrame(data)
    return df

def verify_mwpl_parsing():
    print("--- Starting MWPL Robust Parsing Verification ---")

    # 1. Create mock data
    df = create_mock_mwpl_df()
    print(f"Created mock DataFrame with {len(df)} rows (including garbage headers).")

    # 2. Run Detection
    print("\n[Step 1] Detecting Format...")
    format_info = FieldMapper.detect_format(df)
    print(f"Detected Format: {format_info}")

    if format_info['type'] != 'mwpl':
        print("❌ FAILED: Did not detect 'mwpl' format correctly.")
        return False
    else:
        print("✅ SUCCESS: Detected 'mwpl' format.")

    # 3. Run Mapping
    print("\n[Step 2] Mapping Records...")
    try:
        records = FieldMapper.map_to_records(df, format_info, trade_date=date(2026, 2, 5))
        print(f"Mapped {len(records)} records.")

        # Validation
        expected_count = 9 # 3 stocks * 3 clients (assuming all valid)
        # Note: In our mock, all have data.

        if len(records) == expected_count:
            print(f"✅ SUCCESS: Count matches expected ({expected_count}).")
        else:
            print(f"❌ FAILED: Expected {expected_count} records, got {len(records)}.")
            for r in records[:3]: print(r)
            return False

        # Validate content of first record
        first = records[0]
        if first['underlying_stock'] == 'RELIANCE' and first['client_position_num'] == 1 and first['position_pct'] == 500000.0:
             print("✅ SUCCESS: First record data matches.")
        else:
             print(f"❌ FAILED: First record mismatch: {first}")
             return False

    except Exception as e:
        print(f"❌ CRITICAL ERROR during mapping: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = verify_mwpl_parsing()
    if success:
        print("\n🎉 Verification Passed!")
        sys.exit(0)
    else:
        print("\n💀 Verification Failed!")
        sys.exit(1)
