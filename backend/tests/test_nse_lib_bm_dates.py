import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from backend.ingest.nse_lib import NSELib
import pandas as pd

@patch('backend.ingest.nse_lib.NSELib.get')
@patch('curl_cffi.requests.get')
def test_get_board_meetings_date_filter(mock_cffi_get, mock_get):
    # Mocking NSELib.get for the main API call
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "bm_symbol": "TCS",
            "bm_purpose": "Dividend",
            "bm_desc": "Interim Dividend",
            "bm_date": "15-May-2026"  # Board meeting is on 15 May
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
            "an_dt": "10-May-2026 12:00:00", # Happened BEFORE the board meeting (e.g. from an older quarter)
            "attchmntText": "Tata Consultancy Services Limited has informed the Exchange that Board of Directors at its meeting held on April 9, 2026, recommended Final Dividend of Rs. 10 per equity share."
        },
        {
            "symbol": "TCS",
            "desc": "Dividend",
            "an_dt": "16-May-2026 12:00:00", # Happened AFTER the board meeting!
            "attchmntText": "Tata Consultancy Services Limited has informed the Exchange that Board of Directors at its meeting held on May 15, 2026, recommended Final Dividend of Rs. 31 per equity share."
        }
    ]
    mock_cffi_get.return_value = mock_cffi_resp

    nse = NSELib()
    df = nse.get_board_meetings(date(2026, 4, 1))

    assert not df.empty
    assert df.iloc[0]['SYMBOL'] == 'TCS'
    assert df.iloc[0]['EXTRACTED_DIVIDEND_AMOUNT'] == 31.0 # Should be 31, not 10!
    assert df.iloc[0]['EXTRACTED_DIVIDEND_TYPE'] == 'Final'

if __name__ == '__main__':
    pytest.main(['-v', 'backend/tests/test_nse_lib_bm_dates.py'])
