from backend.ingest.nse_lib import NSELib
import datetime

print("Initializing NSE API connection...")
n = NSELib()

# Testing the date Bharti Airtel announced the Rs 8 dividend
test_date = datetime.date(2024, 5, 9)
print(f"Fetching board meetings for {test_date}...")

df = n.get_board_meetings(test_date)

if not df.empty and 'SYMBOL' in df.columns:
    bharti = df[df['SYMBOL'] == 'BHARTIARTL']
    if not bharti.empty:
        print("\n--- Bharti Airtel Records Found ---")
        for index, row in bharti.iterrows():
            purpose = row.get('PURPOSE', '')
            attachment = row.get('attachment', '')
            amount = row.get('EXTRACTED_DIVIDEND_AMOUNT')

            print(f"Purpose: {purpose}")
            print(f"Attachment URL: {attachment}")
            print(f"Extracted Amount: {amount}")
            print("-" * 40)
    else:
        print("Bharti Airtel not found on this date.")
else:
    print("No data found or SYMBOL column missing.")
