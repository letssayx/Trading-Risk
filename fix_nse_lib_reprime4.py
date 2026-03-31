# The user issue also has: "Contract delta import is failing since early morning today,"
# The problem is that nsearchives is throwing 403 on ALL static files when downloaded by datacenter IPs and non-browsers starting recently.
# My `temp_session` uses `impersonate="chrome120"`. This SHOULD bypass Akamai WAF.
# BUT what if they are doing it for `get_fii_dii_cash` and `get_fao_participant_oi` too?
# Let's see if there's any other place that loops `self.get` and causes the spammy 403 logs.
with open("backend/ingest/nse_lib.py", "r") as f:
    code = f.read()
import re
# check how many times self.get(url) is in a loop
print("Looping gets:", len(re.findall(r'for url in urls:\s*(?:try:\s*)?resp = self\.get\(url\)', code)))
