import requests
from bs4 import BeautifulSoup
from io import StringIO
import pandas as pd

url = "https://www.arihantcapital.com/derivatives/fii-dii-trading-activities"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# 1. GET request for FII
session = requests.Session()
resp = session.get(url, headers=headers)
soup = BeautifulSoup(resp.content, 'html.parser')

# Get ASP.NET hidden fields
viewstate = soup.find(id="__VIEWSTATE")['value']
viewstategenerator = soup.find(id="__VIEWSTATEGENERATOR")['value']

print("Got VIEWSTATE")

# POST for DII
payload = {
    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ddlSubCategory",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__VIEWSTATE": viewstate,
    "__VIEWSTATEGENERATOR": viewstategenerator,
    "ctl00$ContentPlaceHolder1$cattypeid": "cash",
    "ctl00$ContentPlaceHolder1$fosubCatid": "index",
    "ctl00$ContentPlaceHolder1$ddlSubCategory": "DII"
}

resp_dii = session.post(url, data=payload, headers=headers)
soup_dii = BeautifulSoup(resp_dii.content, 'html.parser')

tables = soup_dii.find_all('table')
print(f"Found {len(tables)} tables in DII response.")
if tables:
    try:
        df = pd.read_html(StringIO(str(tables[0])), flavor='bs4')[0]
        print(df.head())
    except Exception as e:
        print("Error reading table", e)
