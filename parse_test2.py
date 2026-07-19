import re

text = """
The Board of Directors has declared a Special Dividend of Rs 24 per equity share.
The Record Date for the purpose of payment of Dividend is Friday, July 24, 2026.
Also 24th July, 2026 is good.
"""

def extract_record_date_from_pdf(text):
    # First pattern: DD-MMM-YYYY
    date_pattern = re.compile(r'(\d{1,2}-[a-zA-Z]{3}-\d{4})')
    date_match = date_pattern.search(text)

    if not date_match:
        # Second pattern: Month DD, YYYY or DD Month YYYY
        date_pattern2 = re.compile(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})', re.IGNORECASE)
        date_match = date_pattern2.search(text)

    if date_match and 'record date' in text.lower():
        # Convert to DD-MMM-YYYY format
        raw_date = date_match.group(1)
        # Parse it just to see if we can easily convert
        from datetime import datetime
        try:
            # Let's just return the raw for now, nse_lib.py might parse it later or we should format it.
            return raw_date
        except:
            pass
        return date_match.group(1)
    return None

print(extract_record_date_from_pdf(text))
