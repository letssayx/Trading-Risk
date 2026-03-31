# If NSE blocked contract delta, maybe the URL changed. Let's see if we can fetch it via API instead of Archives
from curl_cffi import requests
session = requests.Session(impersonate="chrome120")
# The user trace says "Contract delta import is failing since early morning today,"
# The problem is that Contract Delta might have moved to a different path today, OR the user IP got blocked.
# If I can't test because my IP is blocked, I must focus on the error handling in `nse_lib.py`.

# WAIT! Look at nse_lib.py:
# `resp = self.get(url)`
# `if resp and resp.status_code == 200...`
# If we get a 403, `get()` calls `self._ensure_session()`.
# If `self._ensure_session()` fails 3 times, it returns.
# But `get()` says:
# if resp.status_code in (401, 403):
#    logger.warning(f"Got {resp.status_code}, re-priming session...")
#    self._cookies_primed = False
#    self.session.cookies.clear()
#    self._ensure_session()
#    resp = self.session.get(url, timeout=30)
# THIS is what generates the user's log:
# [WARNING] Got 403, re-priming session...
# [INFO] Priming NSE session via https://www.nseindia.com... (Attempt 1)
# [INFO] Session primed successfully.
# THEN the code does `resp = self.session.get(url)` AGAIN for the next URL in the loop!
# Wait! In `get_contract_delta`, there is a loop over `urls`:
# for url in urls:
#    resp = self.get(url)
#
# If EACH URL gets a 403 (because nsearchives doesn't like the cookie we just primed, or is just blocking),
# we re-prime the session FOR EACH URL!
# That explains the log! "Got 403, re-priming session... Session primed successfully." repeated exactly 8 times!
# Because there are 8 URLs in the `urls` list!
