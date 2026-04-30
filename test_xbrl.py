import requests
import xml.etree.ElementTree as ET

symbol = "WIPRO"
url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=5)
res = session.get(url, headers=headers, timeout=5)
data = res.json()
xbrl_url = data[0]['xbrl']
print("XBRL URL:", xbrl_url)

res_xml = session.get(xbrl_url, headers=headers, timeout=5)
root = ET.fromstring(res_xml.text)

for elem in root:
    tag_name = elem.tag.split('}')[-1]
    if tag_name == 'NumberOfShares':
        print(f"NumberOfShares | contextRef: {elem.attrib.get('contextRef')} | text: {elem.text}")
