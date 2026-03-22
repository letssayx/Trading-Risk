import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

match = re.search(r'async function loadDividendsData\(\) \{.*?(?=async function)', content, re.DOTALL)
if match:
    print(match.group(0))
