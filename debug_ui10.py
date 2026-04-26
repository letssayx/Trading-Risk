with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

lines = html.split('\n')
for i, l in enumerate(lines):
    if '<div class="tab-content-area">' in l:
        print(f"Found at line {i+1}: {l}")
        for j in range(max(0, i-5), min(len(lines), i+15)):
             print(f"{j+1}: {lines[j]}")
