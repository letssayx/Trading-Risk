with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

start = html.find('<!-- TAB 1: TERMINAL (Original Workbench) -->')
end = html.find('<!-- TAB AI-ANALYZE -->')
sub = html[start:end]

lines = sub.split('\n')
b = 0
for i, l in enumerate(lines):
    b += l.count("<div") - l.count("</div")
    if b < 0:
        print(f"Negative balance at line {i}: {l}")
