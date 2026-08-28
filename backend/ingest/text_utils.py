import re

def strip_date_fragments(text: str) -> str:
    if not text:
        return ""
    text_lower = text.lower()

    # Strip explicit date formats (dd-MMM-yyyy, dd-MMM-yy, dd/MM/yyyy, dd-MM-yyyy)
    text_lower = re.sub(r'\d{1,2}-[a-z]{3}-\d{2,4}', '', text_lower)
    text_lower = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '', text_lower)
    text_lower = re.sub(r'\d{1,2}-\d{1,2}-\d{2,4}', '', text_lower)

    # Strip Month dd, yyyy (e.g., October 25, 2024)
    text_lower = re.sub(r'(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}', '', text_lower)

    # Strip standalone years bounded by spaces or punctuation (2010 to 2039)
    text_lower = re.sub(r'\b20[1-3][0-9]\b', '', text_lower)

    # Strip ordinal suffixes explicitly used as dates (e.g., 25th August, 1st Jan)
    text_lower = re.sub(r'\d{1,2}(?:st|nd|rd|th)\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{0,4}', '', text_lower)

    # Clean up financial year ending clauses (e.g., "for the period ended March", "ended 31 March")
    text_lower = re.sub(r'ended\s+[a-z]+\s+\d{0,4}', '', text_lower)
    text_lower = re.sub(r'ended\s+\d{1,2}\s+[a-z]+\s+\d{0,4}', '', text_lower)
    text_lower = re.sub(r'f\.y\.?\s*\d{2,4}(?:-\d{2,4})?', '', text_lower)
    text_lower = re.sub(r'financial year\s*\d{2,4}(?:-\d{2,4})?', '', text_lower)

    return text_lower
