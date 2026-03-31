# The user said "Nifty is still a flat line in market activity tab in all charts"
# Let's check Participant OI chart!
# Does it have a Nifty overlay too? The user said "all charts".

import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js_code = f.read()

# Participant OI chart is in `renderParticipantHistorical`
# Let's check if NIFTY is being plotted and if it has zero values
if "renderParticipantHistorical" in js_code:
    print("renderParticipantHistorical found")
    # I should find how NIFTY is rendered there.
