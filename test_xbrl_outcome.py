import requests
import json
import xml.etree.ElementTree as ET

url = "https://www.nseindia.com/api/corporate-announcements?index=equities&from_date=24-03-2026&to_date=25-04-2026&symbol=HDFCAMC"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=10)
response = session.get(url, headers=headers, timeout=10)

if response.status_code == 200:
    data = response.json()
    for item in data:
         print(f"Desc: {item.get('desc')} Seq: {item.get('seq_id')}")
         if item.get("seq_id") == "106591395":
             xbrl_api_url = f"https://www.nseindia.com/api/corporate-announcements-xbrl?seq_id={item['seq_id']}"
             print("Requesting:", xbrl_api_url)
             res_xbrl = session.get(xbrl_api_url, headers=headers)
             print(f"Status: {res_xbrl.status_code}")
             try:
                 print(res_xbrl.json())
             except:
                 print("Not JSON")
