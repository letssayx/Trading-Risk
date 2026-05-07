import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from backend.ingest.nse_lib import NSELib
import pandas as pd

@patch('backend.ingest.nse_lib.NSELib.get')
@patch('curl_cffi.requests.get')
def test_get_board_meetings(mock_cffi_get, mock_get):
    # Mocking NSELib.get for the main API call
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "bm_symbol": "TCS",
            "bm_purpose": "Dividend",
            "bm_desc": "Interim Dividend",
            "bm_date": "15-May-2026"
        }
    ]
    mock_get.return_value = mock_resp

    # Mocking global announcements fetch
    mock_cffi_resp = MagicMock()
    mock_cffi_resp.status_code = 200
    mock_cffi_resp.json.return_value = [
        {
            "symbol": "TCS",
            "desc": "Dividend",
            "attchmntText": "Tata Consultancy Services Limited has informed the Exchange that Board of Directors at its meeting held on April 9, 2026, recommended Final Dividend of Rs. 31 per equity share."
        }
    ]
    mock_cffi_get.return_value = mock_cffi_resp

    nse = NSELib()
    df = nse.get_board_meetings(date(2026, 4, 1))

    assert not df.empty
    assert df.iloc[0]['SYMBOL'] == 'TCS'
    assert df.iloc[0]['EXTRACTED_DIVIDEND_AMOUNT'] == 31.0
    assert df.iloc[0]['EXTRACTED_DIVIDEND_TYPE'] == 'Final'
    assert pd.isna(df.iloc[0]['EXTRACTED_RECORD_DATE']) or df.iloc[0]['EXTRACTED_RECORD_DATE'] is None

if __name__ == '__main__':
    pytest.main(['-v', 'backend/tests/test_nse_lib_bm.py'])
