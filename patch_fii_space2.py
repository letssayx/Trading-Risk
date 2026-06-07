import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

search2 = """                        <!-- FII Position (Contracts and Money) -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 20px;">"""

replace2 = """                        <!-- FII Position (Contracts and Money) -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 10px;">"""

if search2 in content:
    content = content.replace(search2, replace2)
    print("Patched 2")

with open(filepath, 'w') as f:
    f.write(content)
