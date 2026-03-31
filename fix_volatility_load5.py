# If `loadVolatilityAnalysis()` is defined globally at line 3274, it should work.
# Wait. `script_workbench2.js` is included in `<script>` tags without `type="module"`, so functions are globally available.
# But `script_workbench2.js` has `document.addEventListener('DOMContentLoaded', () => { ... }` wrappers?
# Let's check where `loadVolatilityAnalysis` is defined. Is it inside another function?
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

# Let's see if there are missing closing braces before `loadVolatilityAnalysis`
# In javascript, if it was inside a function, `window.loadVolatilityAnalysis` wouldn't exist.
print("Is loadVolatilityAnalysis inside a function block?", "function loadVolatilityAnalysis()" in js)
import re

matches = re.finditer(r'function (\w+)\(', js)
for m in matches:
    if m.group(1) == 'loadVolatilityAnalysis':
        print("Found definition:", js[m.start()-50:m.end()+10])
