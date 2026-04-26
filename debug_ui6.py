with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

start = html.find('<!-- TAB 1: TERMINAL (Original Workbench) -->')
end = html.find('<!-- TAB AI-ANALYZE -->')
sub = html[start:end]

b = 0
for i, l in enumerate(sub.split('\n')):
    b += l.count("<div") - l.count("</div")

print("Overall b:", b)
