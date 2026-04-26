with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

start = html.find('<!-- TAB 1: TERMINAL (Original Workbench) -->')
sub = html[start:]

lines = sub.split('\n')
for i in range(1720, 1740):
    print(f"{i}: {lines[i]}")
