with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

lines = html.split('\n')
bal = 0
for i in range(609, 2115):
    l = lines[i]
    bal += l.count('<div') - l.count('</div')
    if bal == 0:
        print(f"Closed wb-tabs-header (line 610) at line {i+1}: {l.strip()}")
        break
