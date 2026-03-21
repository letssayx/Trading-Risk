import re

with open('backend/web/api/data/view_routes.py', 'r') as f:
    code = f.read()

# Let's inspect line 479 exactly
lines = code.split('\n')
for i, line in enumerate(lines[475:490]):
    print(f"{i+475}: {line}")
