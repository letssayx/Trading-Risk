import re

text = """
The Board of Directors has declared a Special Dividend of Rs 24 per equity share.
The Record Date for the purpose of payment of Dividend is Friday, July 24, 2026.
"""

def extract_record_date_from_pdf(text):
    date_pattern = re.compile(r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4})', re.IGNORECASE)
    date_match = date_pattern.search(text)
    if date_match and 'record date' in text.lower():
        return date_match.group(1)
    return None

print(extract_record_date_from_pdf(text))
