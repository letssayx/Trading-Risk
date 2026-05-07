import requests

url_div = "https://www.nseindia.com/api/corporate-announcements?index=equities&subject=Record Date"
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
}
res_div = requests.get(url_div, headers=headers)
if res_div.status_code == 200:
    data = res_div.json()
    print(len(data))
    print(data[-1]['an_dt'])
