import unittest
import pandas as pd
from datetime import date
from backend.ingest.field_mapper import FieldMapper

class TestMWPLParsing(unittest.TestCase):
    def test_mwpl_with_title_row(self):
        """Test MWPL parsing when the first row is a title/merged cell."""
        data = [
            ['Position as percentage (%) of MWPL', None, None, None, None],
            ['Sr No.', 'Underlying Stock', 'Client 1', 'Client 2', 'Client 3'],
            [1, 'ABCAPITAL', 7.97, 7.79, 6.99],
            [2, 'ADANIENSOL', 7.00, 5.01, 4.51]
        ]
        df = pd.DataFrame(data)

        # Test detection
        format_info = FieldMapper.detect_format(df)
        self.assertEqual(format_info['type'], 'mwpl')

        # Test mapping
        records = FieldMapper.map_to_records(df, format_info, trade_date=date(2026, 2, 5))

        self.assertEqual(len(records), 6) # 2 stocks * 3 clients

        # Check first record details
        self.assertEqual(records[0]['underlying_stock'], 'ABCAPITAL')
        self.assertEqual(records[0]['client_position_num'], 1)
        self.assertEqual(records[0]['position_pct'], 7.97)
        self.assertEqual(records[0]['date'], date(2026, 2, 5))

    def test_mwpl_without_title_row(self):
        """Test MWPL parsing when the first row is the header directly."""
        data = [
            ['Sr No.', 'Underlying Stock', 'Client 1', 'Client 2', 'Client 3'],
            [1, 'ABCAPITAL', 7.97, 7.79, 6.99],
            [2, 'ADANIENSOL', 7.00, 5.01, 4.51]
        ]
        df = pd.DataFrame(data[1:], columns=data[0])

        # Test detection
        format_info = FieldMapper.detect_format(df)
        self.assertEqual(format_info['type'], 'mwpl')

        # Test mapping
        records = FieldMapper.map_to_records(df, format_info, trade_date=date(2026, 2, 5))

        self.assertEqual(len(records), 6) # 2 stocks * 3 clients
        self.assertEqual(records[0]['underlying_stock'], 'ABCAPITAL')

    def test_mwpl_header_search(self):
        """Test if header search works when header is in row 2 (index 2)."""
        data = [
            ['Random Junk', None, None, None, None],
            ['Position as percentage (%) of MWPL', None, None, None, None],
            ['Sr No.', 'Underlying Stock', 'Client 1', 'Client 2', 'Client 3'],
            [1, 'ABCAPITAL', 7.97, 7.79, 6.99]
        ]
        df = pd.DataFrame(data)

        # Test detection
        format_info = FieldMapper.detect_format(df)
        self.assertEqual(format_info['type'], 'mwpl')

        # Test mapping
        records = FieldMapper.map_to_records(df, format_info, trade_date=date(2026, 2, 5))

        self.assertEqual(len(records), 3) # 1 stock * 3 clients
        self.assertEqual(records[0]['underlying_stock'], 'ABCAPITAL')

if __name__ == '__main__':
    unittest.main()
