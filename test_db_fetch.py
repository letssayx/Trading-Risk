import asyncio
from datetime import date
from backend.ingest.nse_lib import NSELib
from backend.ingest.field_mapper import FieldMapper

client = NSELib()
df = client.get_corporate_actions(date(2025, 1, 1))

format_info = FieldMapper.detect_format(df)
print("CA Format:", format_info)
if format_info['type'] == 'unknown':
     format_info = {'type': 'corporate_actions'}

records = FieldMapper.map_to_records(df, format_info, date(2025, 1, 1))
print("CA mapped count:", len(records))
if records:
     print(records[0])

df2 = client.get_board_meetings(date(2025, 1, 1))
format_info2 = FieldMapper.detect_format(df2)
print("BM Format:", format_info2)
if format_info2['type'] == 'unknown':
     format_info2 = {'type': 'board_meetings'}

records2 = FieldMapper.map_to_records(df2, format_info2, date(2025, 1, 1))
print("BM mapped count:", len(records2))
if records2:
    print(records2[0])
