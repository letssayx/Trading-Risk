import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

thead_search = re.search(r'<thead id="mr-data-head">.*?</thead>', html, re.DOTALL)
th_cols = re.findall(r'<th.*?>(.*?)</th>', thead_search.group(0), re.DOTALL)

for i, th in enumerate(th_cols):
    if "200-Day" in th:
        continue
    # print(f"{i}: {th.replace('<br>', ' ').strip()}")

# Wait, there is a th count of 50 in HTML, but the last one is 200-Day EMA. 0-49 = 50.
# The TD count in JS is 47 (excluding the 2 fixed Date/Symbol columns), which makes 49 total.
# 50 - 49 = 1 column missing in JS!

# Let's count properly
