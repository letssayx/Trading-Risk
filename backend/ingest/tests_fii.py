import pandas as pd
from datetime import date
from backend.ingest.field_mapper import FieldMapper

df = pd.DataFrame({
    'trade_date': ['2023-01-01', '2023-01-01'],
    'category': ['FII', 'DII'],
    'buy_value': [100.0, 200.0],
    'sell_value': [50.0, 150.0],
    'net_value': [50.0, 50.0]
})

print(FieldMapper.detect_format(df))
print(FieldMapper.map_to_records(df, {'type': 'fii_dii_cash', 'target_table': 'fii_dii_cash'}, date(2023, 1, 1)))
