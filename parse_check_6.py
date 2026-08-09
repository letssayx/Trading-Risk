import re
text = "REC Limited has informed the Exchange that Record date for the purpose of Payment of finai Dividend for the FY 2025-26 is 14-Aug-2026."
text2 = "REC Limited has informed the Exchange that Record date for the purpose of Dividend is 31-Jul-2026."

print(re.search(r'Record date.*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', text, re.IGNORECASE).group(1))
print(re.search(r'Record date.*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', text2, re.IGNORECASE).group(1))
