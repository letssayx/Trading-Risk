import re
text = "Coal India Limited has informed the Exchange that Record date for the purpose of Dividend  is 04-Sep-2026."
record_date_match = re.search(r'Record date.*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', text, re.IGNORECASE)
print(record_date_match.groups() if record_date_match else None)
