import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

thead_search = re.search(r'<thead id="mr-data-head">.*?</thead>', html, re.DOTALL)
th_cols = re.findall(r'<th.*?>(.*?)</th>', thead_search.group(0), re.DOTALL)

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    js = f.read()

td_search = re.search(r'let html = ``;.*?</tr>', js, re.DOTALL)
td_cols = re.findall(r'<td>(.*?)</td>', td_search.group(0), re.DOTALL)

print(f"TH count: {len(th_cols)}, TD count (excluding fixed): {len(td_cols)}")

for i in range(max(len(th_cols), len(td_cols) + 2)):
    th = th_cols[i] if i < len(th_cols) else 'N/A'
    th = th.replace('<br>', ' ').replace('\n', ' ').strip()
    td = 'N/A'
    if i == 0: td = 'Date'
    elif i == 1: td = 'Symbol'
    elif i - 2 < len(td_cols): td = td_cols[i - 2]
    print(f"{i}: {th:<40} | {td}")
