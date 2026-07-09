import re

with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

# Since the button is removed, we don't strictly need the function `buildDividendDatabank` anymore,
# but we can leave it or remove it. Let's just remove it to be clean.
content = re.sub(r'async function buildDividendDatabank\(\) \{.*?\n\}\n', '', content, flags=re.DOTALL)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(content)
