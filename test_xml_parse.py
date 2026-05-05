import requests
import xml.etree.ElementTree as ET

url = "https://nsearchives.nseindia.com/corporate/xbrl/PIBM_541729_2432026181717_PRIOR_INTIMATION_WebXMLFile_20260324_181720352.xml"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/xml',
}
res = requests.get(url, headers=headers)
print(res.status_code)
root = ET.fromstring(res.content)
for elem in root.iter():
    if "Dividend" in elem.tag:
        print(f"{elem.tag}: {elem.text}")
