import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

# I will replace the block inside `if (snapshotMode) { thead.innerHTML = ... } else { thead.innerHTML = ... }`
# Wait, let's see how `script_workbench2.js` does it!
