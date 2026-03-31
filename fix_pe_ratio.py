# The other one that loops is pe_ratio
import re
with open("backend/ingest/nse_lib.py", "r") as f:
    code = f.read()

# For PE Ratio, the WAF issue might be the same. Let's fix that one too if there's a loop.
# `def get_pe_ratio`
code = code.replace("""        for url in urls:
            resp = self.get(url)
            # Check for 200 OK and explicitly ignore NSE's custom 404 HTML payloads
            if resp and resp.status_code == 200 and b'<!doctype html>' not in resp.content[:1024].lower():
                try:
                    df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                    if not df.empty:
                        # Map to our standard format
                        df.rename(columns={'Symbol': 'symbol', 'Date': 'date'}, inplace=True)
                        return df
                except Exception as e:
                    logger.error(f"Error parsing PE Ratio from {url}: {e}")
        return pd.DataFrame()""",
"""        temp_session = cffi_requests.Session(impersonate="chrome120")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        for url in urls:
            try:
                # If it's a base URL API, use self.get, otherwise use the cookie-less temp session
                if 'www.nseindia.com' in url:
                    resp = self.get(url)
                else:
                    resp = temp_session.get(url, headers=headers, timeout=10)

                # Check for 200 OK and explicitly ignore NSE's custom 404 HTML payloads
                if resp and resp.status_code == 200 and b'<!doctype html>' not in resp.content[:1024].lower():
                    df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                    if not df.empty:
                        # Map to our standard format
                        df.rename(columns={'Symbol': 'symbol', 'Date': 'date'}, inplace=True)
                        return df
            except Exception as e:
                logger.error(f"Error parsing PE Ratio from {url}: {e}")

        return pd.DataFrame()""")

with open("backend/ingest/nse_lib.py", "w") as f:
    f.write(code)
