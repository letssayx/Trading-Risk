import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

thead_search = re.search(r'<thead id="mr-data-head">.*?</thead>', html, re.DOTALL)
th_cols = re.findall(r'<th.*?>(.*?)</th>', thead_search.group(0), re.DOTALL)

for i, th in enumerate(th_cols):
    if "200-Day" in th:
        continue
