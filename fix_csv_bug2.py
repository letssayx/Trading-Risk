# The problem is that `script_workbench2.js` is loaded at the END of `workbench.html`?
# YES! `<script src="/static/js/script_workbench2.js"></script>`
# And the button is `<button onclick="...">`
# In `script_workbench2.js` line 14:
# `const echartInstance = null;`
# But if it has a syntax error, none of the functions are registered globally!
# IS THERE A SYNTAX ERROR in `script_workbench2.js` right now?
# Let's run a node check.
import subprocess

try:
    res = subprocess.run(["node", "-c", "backend/ui/static/js/script_workbench2.js"], capture_output=True, text=True)
    if res.returncode != 0:
        print("SYNTAX ERROR in script_workbench2.js!")
        print(res.stderr)
    else:
        print("No syntax error in script_workbench2.js.")
except Exception as e:
    print("Failed to run node:", e)
