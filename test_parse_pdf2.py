import re
import datetime

def parse_record_date_from_text(text):
    date_patterns = [
        r'(?:record date(?:.*?is)?)\s*(?:[a-zA-Z]+,\s*)?([a-zA-Z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s*\d{4}|\d{1,2}(?:st|nd|rd|th)?[- \.][a-zA-Z]+[- \.]\d{4})',
        r'([a-zA-Z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s*\d{4}|\d{1,2}(?:st|nd|rd|th)?[- \.][a-zA-Z]+[- \.]\d{4})(?=\s*(?:as|for).*?record date)'
    ]
    for pat in date_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None

print(parse_record_date_from_text("The Record Date is Friday, July 24, 2026."))
print(parse_record_date_from_text("The Company has fixed the 'Record Date' as follows: July 24, 2026"))
