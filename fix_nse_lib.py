# The only reliable way to fetch NSE without 403 on some networks is to NOT send a User-Agent that triggers their Akamai protections if the TLS fingerprint doesn't perfectly match.
# Or better, impersonate something more common.
import re

with open("backend/ingest/nse_lib.py", "r") as f:
    code = f.read()

# Make the headers slightly simpler
code = code.replace(
    '"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",',
    '"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",'
)
code = code.replace('impersonate="chrome110"', 'impersonate="chrome120"')

# But wait, the user's issue might be that `_ensure_session` is failing!
# "Got 403, re-priming session... Session primed successfully. Got 403, re-priming session..."
# So the MAIN site primes correctly, but the ARCHIVES site returns 403.
# The `get` method handles 401/403:
# if resp.status_code in (401, 403):
#     logger.warning(f"Got {resp.status_code}, re-priming session...")
#     ...
#     resp = self.session.get(url, timeout=30)
# This loops, or retries once.

# If archives is separate, maybe it doesn't need session priming, or needs different headers?
# Usually nsearchives.nseindia.com DOES NOT NEED COOKIES. It's just a static file server, but it does check User-Agent.
# Actually, nsearchives is on Akamai, and it often rejects requests that HAVE cookies from www.nseindia.com, or it expects NONE, or it expects normal headers.
# In `get()`, we are sending the same session cookies!
# What if we create a separate session for archives? Or we just use standard curl_cffi for archives without cookies?

# Let's verify if `get_contract_delta` works if we don't prime.
