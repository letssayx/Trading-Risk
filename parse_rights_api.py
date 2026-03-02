import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

def test_url(url):
    print(f"Testing {url} ...")
    r = session.get(url, headers=headers)
    if r.ok:
        try:
            data = r.json().get('data', [])
            if not data:
                data = r.json() # Could be a direct array
            if type(data) is list:
                stages = set(x.get('stage') for x in data if type(x) is dict and 'stage' in x)
                print("  Length:", len(data))
                print("  Stages:", stages)
        except Exception as e:
            print("  Returned ok but not expected JSON format", e)
    else:
        print("  Status:", r.status_code)

test_url("https://www.nseindia.com/api/corporate-further-issues-ip-ri")
test_url("https://www.nseindia.com/api/corporate-further-issues?type=in-principle")
test_url("https://www.nseindia.com/api/corporates-in-principle?index=equities")
test_url("https://www.nseindia.com/api/corporate-in-principle")
test_url("https://www.nseindia.com/api/in-principle-ri")
