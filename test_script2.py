import re

purpose = "Bharti Airtel Limited has informed the exchange that record date for the purpose of Dividend is 24-Jul-2026"
has_dividend_mention = 'dividend' in purpose.lower() or 'intdiv' in purpose.lower() or 'findiv' in purpose.lower()
print(has_dividend_mention)

# test checking record date missing
# Let's see nse_lib.py
