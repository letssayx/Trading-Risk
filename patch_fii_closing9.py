import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

fii_tab_start = content.find("<!-- SUB-TAB FII Analysis -->")
mwpl_tab_start = content.find("<!-- SUB-TAB MWPL Analysis -->")

fii_tab_content = content[fii_tab_start:mwpl_tab_start]
open_divs = fii_tab_content.count("<div")
closed_divs = fii_tab_content.count("</div")

if closed_divs > open_divs:
    print(f"Removing {closed_divs - open_divs} extra closing divs from FII tab")
    new_fii_content = fii_tab_content.rstrip()
    for _ in range(closed_divs - open_divs):
        if new_fii_content.endswith("</div>"):
            new_fii_content = new_fii_content[:-6].rstrip()
    content = content[:fii_tab_start] + new_fii_content + "\n\n                " + content[mwpl_tab_start:]
    with open(filepath, 'w') as f:
        f.write(content)
