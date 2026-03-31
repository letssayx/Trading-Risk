# Matrix, Basis, Chain failed. Let's see how their `<div>` is defined in `workbench.html`
with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

import re

for tab in ['matrix', 'basis', 'chain']:
    match = re.search(f'<div[^>]*id="deriv-tab-{tab}"[^>]*>', html)
    if match:
        print(f"Match for {tab}: {match.group(0)}")
    else:
        print(f"No match for {tab}")
