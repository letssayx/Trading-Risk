# The user issue is: "Contract delta import is failing since early morning today"
# If `nsearchives` is returning 403, it means Akamai is blocking the request.
# But NSE recently moved the data to a new location, OR they changed the URL pattern, OR we need to add a fallback!
# If `nsearchives.nseindia.com` blocks, NSE India API `www.nseindia.com/api/` might have the file!
# Let's see if we can add a fallback using `curl_cffi` raw without `session` for nsearchives.
# Wait, let's fix the looping re-prime issue first so it doesn't log 8 times.
# ALSO, maybe `contract_delta` has been moved to a different domain.

import re

with open("backend/ingest/nse_lib.py", "r") as f:
    code = f.read()

# Modify the `get` method so that it doesn't constantly reprime if we hit nsearchives. nsearchives DOES NOT need priming, it just uses WAF.
# Wait, actually, sending NSE INDIA cookies to NSE ARCHIVES sometimes CAUSES the 403!
# Let's fix `get_contract_delta` to not use `self.get(url)` which sends the primed cookies.
# Instead, make a direct raw request to archives using `requests.get` without cookies.

new_get_contract_delta = """    def get_contract_delta(self, trade_date: date) -> pd.DataFrame:
        \"\"\"Get Contract Delta.\"\"\"
        date_str = trade_date.strftime("%d%m%Y")
        urls = [
            f"{self.ARCHIVES_URL}/content/nsccl/Contract_Delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/content/nsccl/contract_delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/Contract_Delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/contract_delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/n_delta_trd_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{date_str}.DAT",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/n_delta_trd_{date_str}.DAT",
            f"{self.BASE_URL}/api/reports?archives=1&date={date_str}&type=delta",  # Fallback
            f"https://archives.nseindia.com/content/nsccl/Contract_Delta_{date_str}.csv", # Sometimes they use archives.nseindia.com
        ]

        # Use a fresh, cookie-less session for archives as sending nseindia cookies sometimes triggers WAF 403s on static files
        temp_session = cffi_requests.Session(impersonate="chrome120")
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
                    df.columns = [str(c).strip() for c in df.columns]
                    if not df.empty:
                        return df
            except Exception as e:
                logger.error(f"Error parsing Contract Delta from {url}: {e}")

        return pd.DataFrame()"""

# Replace the original method
old_get_contract_delta_pattern = r'    def get_contract_delta\(self, trade_date: date\) -> pd\.DataFrame:.*?(?=    def get_fii_dii_cash)'
code = re.sub(old_get_contract_delta_pattern, new_get_contract_delta + "\n\n", code, flags=re.DOTALL)

with open("backend/ingest/nse_lib.py", "w") as f:
    f.write(code)
