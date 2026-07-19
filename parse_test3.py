import re
from datetime import datetime

raw_date = "July 24, 2026"
raw_date2 = "24th July, 2026"
raw_date3 = "24-Jul-2026"

def clean_and_format_date(raw_date):
    clean_date = re.sub(r'(st|nd|rd|th)', '', raw_date, flags=re.IGNORECASE).replace(',', '')
    try:
        # Try DD-MMM-YYYY
        dt = datetime.strptime(clean_date, "%d-%b-%Y")
        return dt.strftime("%d-%b-%Y")
    except ValueError:
        pass

    try:
        # Try Month DD YYYY
        dt = datetime.strptime(clean_date.strip(), "%B %d %Y")
        return dt.strftime("%d-%b-%Y")
    except ValueError:
        pass

    try:
        # Try DD Month YYYY
        dt = datetime.strptime(clean_date.strip(), "%d %B %Y")
        return dt.strftime("%d-%b-%Y")
    except ValueError:
        pass

    try:
        # Try Mon DD YYYY
        dt = datetime.strptime(clean_date.strip(), "%b %d %Y")
        return dt.strftime("%d-%b-%Y")
    except ValueError:
        pass

    try:
        # Try DD Mon YYYY
        dt = datetime.strptime(clean_date.strip(), "%d %b %Y")
        return dt.strftime("%d-%b-%Y")
    except ValueError:
        pass

    return raw_date

print(clean_and_format_date(raw_date))
print(clean_and_format_date(raw_date2))
print(clean_and_format_date(raw_date3))
