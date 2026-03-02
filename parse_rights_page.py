import requests
import re

url = "https://www.nseindia.com/companies-listing/corporate-filings-actions"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers)
response = session.get(url, headers=headers)

# Let's find any mentions of "in-principle" or "rights" or "further-issues" inside the source code
# Sometimes these are embedded in JS strings.
scripts = re.findall(r'<script.*?</script>', response.text, re.DOTALL | re.IGNORECASE)

for match in re.finditer(r'api/[a-zA-Z0-9_\-]+', response.text):
    print(match.group())
