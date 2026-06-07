import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

body_start = content.find("<body>")
body_end = content.find("</body>")

body_content = content[body_start:body_end]
open_divs = body_content.count("<div")
closed_divs = body_content.count("</div")

if closed_divs > open_divs:
    print(f"Removing {closed_divs - open_divs} extra closing divs from body")
    idx = content.rfind("</div>", 0, body_end)
    content = content[:idx] + content[idx+6:]
    with open(filepath, 'w') as f:
        f.write(content)
