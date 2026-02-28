import pandas as pd
import io
import sys
import os
import unittest
from datetime import date

# Add repo root to path
sys.path.append(os.getcwd())
from backend.ingest.field_mapper import FieldMapper
from backend.ingest.date_utils import parse_nse_date

class TestAvgPriceParsing(unittest.TestCase):

    def test_eq_bhavcopy_avg_price(self):
        csv_data = """TradDt	BizDt	Sgmt	Src	FinInstrmTp	FinInstrmId	ISIN	TckrSymb	SctySrs	XpryDt	FininstrmActlXpryDt	StrkPric	OptnTp	FinInstrmNm	OpnPric	HghPric	LwPric	ClsPric	LastPric	PrvsClsgPric	UndrlygPric	SttlmPric	OpnIntrst	ChngInOpnIntrst	TtlTradgVol	TtlTrfVal	TtlNbOfTxsExctd	SsnId	NewBrdLotQty	Rmks	VWAP	Rsvd1	Rsvd2	Rsvd3	Rsvd4
18-02-2026	18-02-2026	CM	NSE	STK	16921	INE144J01027	20MICRONS	EQ					20 MICRONS LTD	184.55	186.34	181	181.95	183.25	184.77		181.95			62050	11371485.3	1933	F1	1		183.25
"""
        df = pd.read_csv(io.StringIO(csv_data), sep='\t')
        fmt = FieldMapper.detect_format(df)
        self.assertEqual(fmt['type'], 'cm_udiff')
        records = FieldMapper.map_to_records(df, fmt, parse_nse_date("18-02-2026"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['symbol'], '20MICRONS')
        self.assertEqual(records[0]['avg_price'], 183.25)

    def test_eq_old_avg_price(self):
        csv_data = """SYMBOL	SERIES	DATE1	PREV_CLOSE	OPEN_PRICE	HIGH_PRICE	LOW_PRICE	LAST_PRICE	CLOSE_PRICE	AVG_PRICE	TTL_TRD_QNTY	TURNOVER_LACS	NO_OF_TRADES	DELIV_QTY	DELIV_PER
20MICRONS	EQ	18-Feb-2026	184.55	186.34	181	181.95	183.25	184.77	183.25	62050	11371485.3	1933	44605	71.88
"""
        df = pd.read_csv(io.StringIO(csv_data), sep='\t')
        fmt = FieldMapper.detect_format(df)
        self.assertEqual(fmt['type'], 'eq_old')
        records = FieldMapper.map_to_records(df, fmt, parse_nse_date("18-02-2026"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['symbol'], '20MICRONS')
        self.assertEqual(records[0]['avg_price'], 183.25)

if __name__ == '__main__':
    unittest.main()
