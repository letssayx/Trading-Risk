import pandas as pd
from backend.ingest.field_mapper import FieldMapper
df = pd.DataFrame(columns=['trade_date', 'category', 'buy_value', 'sell_value', 'net_value'])
print(FieldMapper.detect_format(df))
