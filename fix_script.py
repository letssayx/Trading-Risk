import re

subject = "Bharti Airtel Limited has informed the exchange that record date for the purpose of Dividend is 24-Jul-2026"
has_dividend_mention = 'dividend' in subject.lower() or 'intdiv' in subject.lower() or 'findiv' in subject.lower() or 'record date' in subject.lower()

print(f"has_dividend_mention: {has_dividend_mention}")
