import pytest
from datetime import date
import pandas as pd
from backend.ingest.field_mapper import FieldMapper

def test_fii_dii_cash_mapping():
    df = pd.DataFrame([
        {
            'trade_date': date(2026, 3, 13),
            'category': 'FII',
            'buy_value': 100.5,
            'sell_value': 50.2,
            'net_value': 50.3
        }
    ])

    format_info = FieldMapper.detect_format(df)
    assert format_info['type'] == 'fii_dii_cash'

    records = FieldMapper.map_to_records(df, format_info, date(2026, 3, 13))
    assert len(records) == 1
    assert records[0]['category'] == 'FII'
    assert records[0]['buy_value'] == 100.5
