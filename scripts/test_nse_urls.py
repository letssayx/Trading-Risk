import requests
from datetime import datetime

BASE_URL = "https://nsearchives.nseindia.com"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

TEST_DATE = datetime(2026, 2, 20)
FORMATS = {
    "dmY": TEST_DATE.strftime("%d%m%Y"),
    "d-m-Y": TEST_DATE.strftime("%d-%m-%Y"),
    "Ymd": TEST_DATE.strftime("%Y%m%d"),
    "d-b-Y": TEST_DATE.strftime("%d-%b-%Y"),
}

PATHS = [
    # Deals
    "content/equities/bulk_deals_{}.csv",
    "archives/equities/mto/bulk_deals_{}.csv",
    "products/content/bulk_deals_{}.csv",
    "content/equities/bulkdeals/bulk_deals_{}.csv",

    # PE
    "products/content/PE_{}.csv",
    "content/indices/PE_{}.csv",

    # Security
    "archives/common/NSE_CM_security_{}.csv.gz",
    "content/common/NSE_CM_security_{}.csv.gz",
    "products/content/NSE_CM_security_{}.csv.gz",
]

def test():
    for path_template in PATHS:
        for fmt_name, dt_str in FORMATS.items():
            path = path_template.format(dt_str)
            url = f"{BASE_URL}/{path}"
            try:
                resp = requests.head(url, headers=HEADERS, timeout=3)
                ctype = resp.headers.get('Content-Type', '')
                if resp.status_code == 200 and 'html' not in ctype:
                    print(f"FOUND! {url}")
            except:
                pass

if __name__ == "__main__":
    test()
