import re
purpose = "Dividend/Other business matters"
has_dividend_mention = 'dividend' in purpose.lower() or 'intdiv' in purpose.lower() or 'findiv' in purpose.lower()
print(has_dividend_mention)
