import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

num_open = content.count("<div")
num_closed = content.count("</div")
print(f"Open: {num_open}, Closed: {num_closed}")
