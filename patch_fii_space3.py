import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

search = """                        <!-- Historical Smart Money Net Pos Table (Reproduced from Market Activity) -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 20px;">"""

replace = """                        <!-- Historical Smart Money Net Pos Table (Reproduced from Market Activity) -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 10px;">"""

if search in content:
    content = content.replace(search, replace)
    print("Patched 1")

search2 = """                        <!-- FII Position Contracts & Money History Table -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 20px;">"""

replace2 = """                        <!-- FII Position Contracts & Money History Table -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 10px;">"""

if search2 in content:
    content = content.replace(search2, replace2)
    print("Patched 2")

search3 = """                        <!-- FII Position (Contracts and Money) -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 20px;">"""

replace3 = """                        <!-- FII Position (Contracts and Money) -->
                        <div class="table-wrapper" style="display: block; border: 1px solid #333; border-radius: 4px; max-width: 100%; margin-bottom: 10px;">"""

if search3 in content:
    content = content.replace(search3, replace3)
    print("Patched 3")

with open(filepath, 'w') as f:
    f.write(content)
