# The user trace says "Got 403, re-priming session..."
# Is it possible the URL is completely wrong or that NSE changed the domain to something else today?
# e.g., https://nsearchives.nseindia.com -> https://www.nseindia.com/api/reports ?
# Or maybe the date formatting?
# Let's try today's date (Mar 31 2026, or Mar 30)
# But even for 28032025 it's 403 instead of 404! This implies Akamai WAF blocked us before even checking if the file exists.
# We are running inside a Sandbox. The Sandbox's IP is likely a datacenter IP (AWS, GCP, etc.).
# Akamai blocks datacenter IPs from nsearchives! That's why we get 403 on literally everything.
# The user's machine IS getting 403s! "Contract delta import is failing since early morning today,"
# The user is probably running from home or a VPS and their IP got flagged, OR NSE rolled out stricter WAF rules today!

# How to bypass Akamai WAF for NSE Archives?
# Sometimes `curl` works if we strip ALL headers.
import subprocess
print("Stripped:", subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"], capture_output=True, text=True).stdout)
