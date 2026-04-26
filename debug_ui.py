import re

with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# find out where exactly the div structure is broken by printing div balances within major elements
# tab-content-area should be 0 balance within itself.
start = html.find('<div class="tab-content-area">')
if start == -1:
    print("Cannot find tab-content-area")
else:
    # go till the end of the file and find the matching closing div for tab-content-area
    balance = 0
    # simple stack
    for m in re.finditer(r'</?div[^>]*>', html[start:]):
        tag = m.group(0)
        is_close = tag.startswith('</div')
        if is_close:
            balance -= 1
        else:
            balance += 1

        if balance == 0:
            print("Found closing div for tab-content-area at offset", m.start() + start)
            end = m.start() + start + len(tag)
            # print what comes after it
            print("Next 200 chars:")
            print(html[end:end+200])
            break
