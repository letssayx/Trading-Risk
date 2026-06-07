import pytest
from datetime import datetime, date

def test_ex_awaited_logic():
    # simulate reliance where amount is declared but date is not yet announced
    history = [{
        'amount': 10.0,
        'ex_date': 'Record date not yet declared',
        'dividend_type': 'Interim'
    }]

    latest = history[0]
    latest_ex_date = latest.get('ex_date')
    is_ex_awaited = False

    if latest_ex_date is None or latest_ex_date == 'Record date not yet declared' or latest_ex_date == '-' or latest_ex_date == '':
        is_ex_awaited = True
    elif isinstance(latest_ex_date, str):
        try:
            datetime.strptime(latest_ex_date, "%d-%b-%Y")
            is_ex_awaited = False
        except ValueError:
            is_ex_awaited = True

    assert is_ex_awaited == True

    # Test when actual date exists
    history2 = [{
        'amount': 10.0,
        'ex_date': '05-Jun-2026',
        'dividend_type': 'Interim'
    }]

    latest2 = history2[0]
    latest_ex_date2 = latest2.get('ex_date')
    is_ex_awaited2 = False
    if latest_ex_date2 is None or latest_ex_date2 == 'Record date not yet declared' or latest_ex_date2 == '-' or latest_ex_date2 == '':
        is_ex_awaited2 = True
    elif isinstance(latest_ex_date2, str):
        try:
            datetime.strptime(latest_ex_date2, "%d-%b-%Y")
            is_ex_awaited2 = False
        except ValueError:
            is_ex_awaited2 = True

    assert is_ex_awaited2 == False

print("Tests ran")
