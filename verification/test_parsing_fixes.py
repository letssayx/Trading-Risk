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

class TestParsingFixes(unittest.TestCase):

    def test_eq_bhavcopy_parsing(self):
        csv_data = """TradDt	BizDt	Sgmt	Src	FinInstrmTp	FinInstrmId	ISIN	TckrSymb	SctySrs	XpryDt	FininstrmActlXpryDt	StrkPric	OptnTp	FinInstrmNm	OpnPric	HghPric	LwPric	ClsPric	LastPric	PrvsClsgPric	UndrlygPric	SttlmPric	OpnIntrst	ChngInOpnIntrst	TtlTradgVol	TtlTrfVal	TtlNbOfTxsExctd	SsnId	NewBrdLotQty	Rmks	Rsvd1	Rsvd2	Rsvd3	Rsvd4
18-02-2026	18-02-2026	CM	NSE	STK	16921	INE144J01027	20MICRONS	EQ					20 MICRONS LTD	184.55	186.34	181	181.95	183.25	184.77		181.95			62050	11371485.3	1933	F1	1
"""
        df = pd.read_csv(io.StringIO(csv_data), sep='\t')
        fmt = FieldMapper.detect_format(df)
        self.assertEqual(fmt['type'], 'cm_udiff')
        records = FieldMapper.map_to_records(df, fmt, parse_nse_date("18-02-2026"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['symbol'], '20MICRONS')

    def test_fo_bhavcopy_parsing(self):
        csv_data = """TradDt	BizDt	Sgmt	Src	FinInstrmTp	FinInstrmId	ISIN	TckrSymb	SctySrs	XpryDt	FininstrmActlXpryDt	StrkPric	OptnTp	FinInstrmNm	OpnPric	HghPric	LwPric	ClsPric	LastPric	PrvsClsgPric	UndrlygPric	SttlmPric	OpnIntrst	ChngInOpnIntrst	TtlTradgVol	TtlTrfVal	TtlNbOfTxsExctd	SsnId	NewBrdLotQty	Rmks	Rsvd1	Rsvd2	Rsvd3	Rsvd4
18-02-2026	18-02-2026	FO	NSE	STO	76102		ABCAPITAL		28-04-2026	28-04-2026	360	PE	ABCAPITAL26APR360PE	0	0	0	29	0	29	349.55	22.55	0	0	0	0	0	F1	3100
18-02-2026	18-02-2026	FO	NSE	STO	57415		ABCAPITAL		24-02-2026	24-02-2026	385	CE	ABCAPITAL26FEB385CE	0.25	0.25	0.2	0.2	0.2	0.35	349.55	0.2	523900	-12400	19	22689520	16	F1	3100
"""
        df = pd.read_csv(io.StringIO(csv_data), sep='\t')
        fmt = FieldMapper.detect_format(df)
        self.assertEqual(fmt['type'], 'fo_udiff')
        records = FieldMapper.map_to_records(df, fmt, parse_nse_date("18-02-2026"))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['ticker_symb'], 'ABCAPITAL')

    def test_mwpl_parsing(self):
        csv_data = """Position as percentage (%) of MWPL
Sr No.	Underlying Stock	Client 1	Client 2	Client 3	Client 4	Client 5	Client 6	Client 7	Client 8	Client 9	Client 10	Client 11	Client 12	Client 13	Client 14	Client 15
1	ABCAPITAL	7.97	7.79	6.99	5.42	3.52	3.41	3.26
2	ADANIENSOL	7.00	5.01	4.51	4.04	4.00	3.22	3.16
"""
        # Header row skip handled by NSELib/Caller usually, but here simulating raw read
        df = pd.read_csv(io.StringIO(csv_data), sep='\t', header=1)
        fmt = FieldMapper.detect_format(df)
        self.assertEqual(fmt['type'], 'mwpl')
        records = FieldMapper.map_to_records(df, fmt, parse_nse_date("18-02-2026"))
        self.assertTrue(len(records) >= 2)

    def test_pe_ratio_parsing(self):
        csv_data = """SYMBOL	SYMBOL P/E	ADJUSTED P/E
THERMAX	50.88	54.17
WHEELS	16.37	16.37
"""
        df = pd.read_csv(io.StringIO(csv_data), sep='\t')
        fmt = FieldMapper.detect_format(df)
        self.assertEqual(fmt['type'], 'pe_ratio')
        records = FieldMapper.map_to_records(df, fmt, parse_nse_date("18-02-2026"))
        self.assertEqual(len(records), 2)

    def test_mto_parsing(self):
        csv_data = """Record Type,Sr No,Name of Security,Quantity Traded,Deliverable Quantity(gross across client level),% of Total Traded Quantity
20,1,20MICRONS,62050,44605,71.88
20,2,360ONE,141381,66419,46.98
"""
        df = pd.read_csv(io.StringIO(csv_data))
        fmt = FieldMapper.detect_format(df)
        self.assertEqual(fmt['type'], 'mto')
        records = FieldMapper.map_to_records(df, fmt, parse_nse_date("18-02-2026"))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['security_name'], '20MICRONS')

if __name__ == '__main__':
    unittest.main()
