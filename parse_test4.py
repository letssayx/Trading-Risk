import re
from datetime import datetime

text = """
The Board of Directors has declared a Special Dividend of Rs 24 per equity share.
The Record Date for the purpose of payment of Dividend is Friday, July 24, 2026.
Also 24th July, 2026 is good.
"""

def extract_record_date_from_text(text):
    date_pattern = re.compile(r'(\d{1,2}-[a-zA-Z]{3}-\d{4})')
    date_match = date_pattern.search(text)

    if not date_match:
        date_pattern2 = re.compile(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})', re.IGNORECASE)
        date_match = date_pattern2.search(text)

    if date_match and 'record date' in text.lower():
        raw_date = date_match.group(1)
        clean_date = re.sub(r'(st|nd|rd|th)', '', raw_date, flags=re.IGNORECASE).replace(',', '')

        for fmt in ["%d-%b-%Y", "%B %d %Y", "%d %B %Y", "%b %d %Y", "%d %b %Y"]:
            try:
                dt = datetime.strptime(clean_date.strip(), fmt)
                return dt.strftime("%d-%b-%Y")
            except ValueError:
                pass

        return raw_date
    return None

print(extract_record_date_from_text(text))
