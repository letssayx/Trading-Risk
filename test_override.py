import requests

with open('dummy.xml', 'w') as f:
    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:in-capmkt="http://www.nseindia.com">
    <in-capmkt:NSESymbol>MPHASIS</in-capmkt:NSESymbol>
    <in-capmkt:DateOfBoardMeeting>29-Apr-2026</in-capmkt:DateOfBoardMeeting>
    <in-capmkt:RateOfFinalDividendRecommendedPerEquityShare>57.00</in-capmkt:RateOfFinalDividendRecommendedPerEquityShare>
    <in-capmkt:RecordDateOfFinalDividendRecommended>09-Jul-2025</in-capmkt:RecordDateOfFinalDividendRecommended>
</root>''')

files = {'file': ('dummy.xml', open('dummy.xml', 'rb'), 'text/xml')}
resp = requests.post('http://127.0.0.1:8000/api/data/board-meetings/override-xml', files=files)
print(resp.status_code)
print(resp.json())
