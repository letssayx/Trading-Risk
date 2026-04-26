with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

lines = html.split('\n')
bal = 0
for i in range(377, 2115):
    l = lines[i]
    if '<div class="wb-tabs-header"' in l:
        print(f"Header at {i+1}: {l.strip()}")
