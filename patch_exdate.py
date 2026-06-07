import re
import os

filepath = 'backend/web/api/data/special_sit_routes.py'
with open(filepath, 'r') as f:
    content = f.read()

search = """            # If the last event is Ex-Awaited (amount declared, but no ex-date yet)
            if history:
                latest = history[0]
                if latest.get('amount') and (not latest.get('ex_date') or latest.get('ex_date') == 'Record date not yet declared'):
                    expected_amount = latest['amount']
                    expected_amount_compare = latest['amount']
                    expected_type = latest.get('dividend_type', 'Interim')"""

replace = """            # If the last event is Ex-Awaited (amount declared, but no ex-date yet)
            if history:
                latest = history[0]
                # Check if amount exists and ex_date is strictly missing or indicates an awaited status
                latest_ex_date = latest.get('ex_date')
                is_ex_awaited = False
                if latest_ex_date is None or latest_ex_date == 'Record date not yet declared' or latest_ex_date == '-' or latest_ex_date == '':
                    is_ex_awaited = True
                elif isinstance(latest_ex_date, str):
                    # If it's a date string but it's an active/past date, it's NOT ex-awaited
                    try:
                        datetime.strptime(latest_ex_date, "%d-%b-%Y")
                        is_ex_awaited = False # It is a valid date string
                    except ValueError:
                        is_ex_awaited = True # Invalid format, assume awaited

                if latest.get('amount') and is_ex_awaited:
                    expected_amount = latest['amount']
                    expected_amount_compare = latest['amount']
                    expected_type = latest.get('dividend_type', 'Interim')"""

if search in content:
    content = content.replace(search, replace)
    with open(filepath, 'w') as f:
        f.write(content)
    print("special_sit_routes.py patched for Reliance logic")
else:
    print("Could not find the target block in special_sit_routes.py")
