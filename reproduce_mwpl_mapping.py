
import pandas as pd
from backend.ingest.field_mapper import FieldMapper

def test_mwpl_mapping_simulation():
    # Simulate pd.read_excel(header=None) output for MWPL file
    # Columns are integers 0, 1, 2...
    data = [
        ["National Stock Exchange of India Ltd", None, None, None, None, None],
        ["Market Wide Position Limit", None, None, None, None, None],
        ["Underlying Stock", "Client 1", "Client 2", "Client 3", "Client 4", "Client 5"],
        ["RELIANCE", 100, 200, 300, 400, 500],
        ["TCS", 150, 250, 350, 450, 550]
    ]
    df = pd.DataFrame(data)

    print("--- Simulated DataFrame (header=None) ---")
    print(df.head())
    print("Columns:", df.columns.tolist())

    # Run mapping
    print("\n--- Running FieldMapper._map_mwpl ---")
    try:
        records = FieldMapper._map_mwpl(df, trade_date=None)
        print(f"Mapped {len(records)} records.")
        if len(records) > 0:
            print("Sample record:", records[0])
            # Check correctness
            expected_first = {'date': None, 'underlying_stock': 'RELIANCE', 'client_position_num': 1, 'position_pct': 100.0}
            assert records[0] == expected_first, f"Expected {expected_first}, got {records[0]}"
            print("SUCCESS: Record matches expected.")
        else:
            print("FAILURE: No records mapped.")
    except Exception as e:
        print(f"ERROR: Mapping failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mwpl_mapping_simulation()
