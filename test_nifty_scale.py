# The user issue says "Nifty is still a flat line in market activity tab in all charts"
# Looking at `renderParticipantHistorical` for Participant OI:
# `niftyData = data.nifty_prices || data.nifty_close || [];`
# `yAxis[1]` has `scale: true`. ECharts usually scales fine with `scale: true`, EXCEPT when there are `0` values.
# If `niftyData` has `0` in it, the minimum goes to 0, and the NIFTY line (around 20,000) looks flat.
# In `cash_flow` I just fixed `0.0` to `None`.
# Does `participant-oi` API also return `0` for NIFTY? Let's check `backend/web/api/analysis_routes.py`
import re
with open("backend/web/api/analysis_routes.py", "r") as f:
    code = f.read()
if "participant-oi" in code:
    print("Found participant-oi")
