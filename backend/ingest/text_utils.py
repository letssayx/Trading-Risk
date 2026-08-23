import re

def strip_date_fragments(text: str) -> str:
    """
    Aggressively removes dates and date-context numbers to prevent date fragments
    from being parsed as amounts. Removes:
    - Calendar dates like '08-May-2023', '27-Apr'
    - Explicit phrases indicating ex-dates, record dates, etc., and the numbers around them.
    - Face value contexts.
    """
    if not text:
        return ""

    clean_text = text

    # 1. Remove calendar date formats
    clean_text = re.sub(r'(\d{1,2}(?:st|nd|rd|th)?\s*[-/]?\s*(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s*[-/]?\s*(?:\d{2,4})?)', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'(\d{4}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{1,2})', '', clean_text)
    clean_text = re.sub(r'(\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4})', '', clean_text)

    # 2. Remove specific date/event phrases that precede numbers
    date_phrases = [
        r'ex-date', r'ex date', r'record date', r'book closure',
        r'bc start date', r'bc end date', r'nd start date', r'nd end date',
        r'held on', r'dated', r'day of'
    ]
    for phrase in date_phrases:
        # Match the phrase, followed by optional punctuation/spaces, followed by numbers
        pattern = rf"{phrase}[:\-\s]*\d{{1,2}}[:\-\s]*\d{{0,4}}"
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)

    # 3. Aggressively remove 'face value' and 'fv' context blocks
    clean_text = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9|~)*\s*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', clean_text, flags=re.IGNORECASE)

    return clean_text

def is_valid_dividend_amount(amount_str: str) -> bool:
    """
    Checks if a parsed string looks like a valid dividend amount, rejecting
    4-digit years (like 2024, 1998).
    """
    if not amount_str:
        return False
    # Reject things that look exactly like years
    if re.match(r'^(19|20)\d{2}$', amount_str.strip()):
        return False

    try:
        val = float(amount_str)
        if val > 1000: # Sanity bound: Dividends > 1000 are extremely rare, likely a misparse
            return False
        return True
    except ValueError:
        return False
