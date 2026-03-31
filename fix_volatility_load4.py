# If it's perfectly valid Javascript, maybe there is a variable scope issue.
# `let volPreExpiryChart = null;` is at the top level of `script_workbench2.js`?
# Wait! In `workbench.html`, I see `onclick="if(window.volPreExpiryChart) ..."`
# If `let` is used in a module or inside an IIFE, it's not on `window`.
# `script_workbench2.js` is included in `<script src="/static/js/script_workbench2.js"></script>`
# `let` variables at the top level of a `<script>` are global, but maybe it's not triggering because `script_workbench2.js` has a syntax error EARLIER in the file, preventing the whole file from loading!
# "No error, its dead button" -> "Load button feels like dead" -> The user specifically mentioned Adv. Technicals having an error, but Volatility button having no error! If the file failed to load, Adv. Technicals wouldn't have thrown a specific map error on `data.macd_hist`, it would say `loadDynamicChart is not defined`.
# So the file IS loading!
# Why would `loadVolatilityAnalysis` do NOTHING?
# Is it attached? Yes, `<button onclick="loadVolatilityAnalysis()">`
# Is `loadVolatilityAnalysis` wrapped inside `document.addEventListener('DOMContentLoaded', function() { ... })`?
import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

print("DOMContentLoaded wrap:", "loadVolatilityAnalysis" in js[js.find('DOMContentLoaded'):])
