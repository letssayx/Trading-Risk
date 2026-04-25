import re

def update_view_routes():
    with open('backend/web/api/data/view_routes.py', 'r') as f:
        content = f.read()

    if "def get_shareholding" not in content:
        import_stmt = "from fastapi import APIRouter, Depends, Query, HTTPException, Request\nimport requests\nfrom bs4 import BeautifulSoup\nimport yfinance as yf\n"

        new_route = """

@router.get("/api/data/fundamentals/shareholding/{symbol}")
def get_shareholding(symbol: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        res = requests.get(f"https://www.screener.in/company/{symbol}/consolidated/", headers=headers, timeout=10)
        if res.status_code != 200:
            res = requests.get(f"https://www.screener.in/company/{symbol}/", headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Look for shareholding table
            sh_table = soup.find('section', id='shareholding')
            if sh_table:
                promoter_pct = 0
                fii_pct = 0
                dii_pct = 0
                public_pct = 0
                rows = sh_table.find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        label = tds[0].text.strip().lower()
                        # Get the latest quarter's value (last column)
                        val_str = tds[-1].text.strip().replace('%', '')
                        try:
                            val = float(val_str)
                        except ValueError:
                            continue

                        if 'promoter' in label:
                            promoter_pct = val
                        elif 'fii' in label:
                            fii_pct = val
                        elif 'dii' in label:
                            dii_pct = val
                        elif 'public' in label:
                            public_pct = val

                # Fetch total outstanding shares from YFinance as a fallback for total shares
                try:
                    ticker = yf.Ticker(f"{symbol}.NS")
                    info = ticker.info
                    total_shares = info.get('sharesOutstanding', 0)
                except Exception:
                    total_shares = 0

                if total_shares > 0:
                    return {
                        "promoter": (promoter_pct / 100) * total_shares,
                        "fii": (fii_pct / 100) * total_shares,
                        "dii": (dii_pct / 100) * total_shares,
                        "retail": (public_pct / 100) * total_shares,
                        "total": total_shares
                    }
    except Exception as e:
        print(f"Screener error: {e}")
        pass

    # YFinance Fallback
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        total_shares = info.get('sharesOutstanding', 0)
        promoters_pct = info.get('heldPercentInsiders', 0)
        institutions_pct = info.get('heldPercentInstitutions', 0)

        if total_shares > 0:
             return {
                 "promoter": promoters_pct * total_shares,
                 "fii": institutions_pct * total_shares * 0.5, # Rough approx if split unknown
                 "dii": institutions_pct * total_shares * 0.5,
                 "retail": (1 - promoters_pct - institutions_pct) * total_shares,
                 "total": total_shares
             }
    except Exception as e:
         print(f"YFinance error: {e}")

    return {"error": "Could not fetch shareholding data"}
"""
        content = content.replace("from fastapi import APIRouter", import_stmt + "from fastapi import APIRouter")
        content += new_route
        with open('backend/web/api/data/view_routes.py', 'w') as f:
            f.write(content)
            print("Successfully updated view_routes.py")

update_view_routes()
