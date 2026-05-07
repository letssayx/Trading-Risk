import pandas as pd
import sys
sys.path.append('.')

df = pd.DataFrame([
    {'SYMBOL': 'LT', 'PURPOSE': 'Board Meeting Intimation', 'EXTRACTED_DIVIDEND_AMOUNT': 38.0, 'EXTRACTED_RECORD_DATE': '22-May-2026', 'MEETING DATE': '05-May-2026'},
    {'SYMBOL': 'LT', 'PURPOSE': 'Financial Results/Dividend', 'EXTRACTED_DIVIDEND_AMOUNT': 38.0, 'EXTRACTED_RECORD_DATE': '22-May-2026', 'MEETING DATE': '05-May-2026'}
])

from backend.ingest.nse_importer import deduplicate_board_meetings
try:
    df_dedup = deduplicate_board_meetings(df)
    print("Deduplicated length:", len(df_dedup))
    print(df_dedup[['SYMBOL', 'PURPOSE']])
except Exception as e:
    print(e)
