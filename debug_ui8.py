with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

start = html.find('<!-- TAB AI-ANALYZE -->')
end = html.find('<!-- TAB DERIVATIVES -->')
sub = html[start:end]

lines = sub.split('\n')
for i, l in enumerate(lines):
    if '</div>' in l:
        print(f"{i}: {l.strip()}")
