with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

lines = html.split('\n')
bal = 0
for i, l in enumerate(lines):
    if '<div class="tab-content-area">' in l:
        print("Starting tab-content-area at line", i+1)
        start = i
        break

bal = 0
for i in range(start, len(lines)):
    l = lines[i]
    bal += l.count('<div') - l.count('</div')
    if bal == 0:
        print(f"Closed tab-content-area at line {i+1}: {l.strip()}")
        break
