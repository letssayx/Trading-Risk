with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

start = html.find('<!-- TAB 1: TERMINAL (Original Workbench) -->')
end = html.find('<!-- TAB AI-ANALYZE -->')
sub = html[start:end]

lines = sub.split('\n')
for i, line in enumerate(lines):
    if "div" in line:
        print(f"{i}: {line.strip()}")
        if i > 50:
            break
