import re
import datetime

def parse_record_date_from_text(text):
    # Try multiple formats
    # Format: 14-May-2026 or 14 May 2026 or 14th May 2026
    date_patterns = [
        r'(?:record date(?:.*?is)?)\s*(\d{1,2}(?:st|nd|rd|th)?[- \.](?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[- \.]\d{4})',
        r'(\d{1,2}(?:st|nd|rd|th)?[- \.](?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[- \.]\d{4})(?=\s*(?:as|for).*?record date)'
    ]
    for pat in date_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None

print(parse_record_date_from_text("The Record Date is Friday, July 24, 2026."))
