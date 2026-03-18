import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

thead_search = re.search(r'<thead id="mr-data-head">.*?</thead>', html, re.DOTALL)
th_cols = re.findall(r'<th.*?>(.*?)</th>', thead_search.group(0), re.DOTALL)

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    js = f.read()

match = re.search(r'if \(\!snapshotMode\) \{[\s\S]*?thead\.innerHTML = `(.*?)`;', js, re.DOTALL)
if match:
    new_js_thead = thead_search.group(0).replace('<thead id="mr-data-head">', '').replace('</thead>', '')
    js = js[:match.start(1)] + new_js_thead + js[match.end(1):]
    with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
        f.write(js)
    print("Replaced JS dynamic header!")
else:
    print("Could not find dynamic JS header in script.")
